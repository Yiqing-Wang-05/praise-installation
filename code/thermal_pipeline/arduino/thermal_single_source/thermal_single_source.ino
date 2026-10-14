#include <Wire.h>
#include <Adafruit_MLX90640.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Independent single-source tracking test for one tea candle.
// Raw centroid x/y stay in sensor coordinates. The fixed mounting maps sensor
// y to canonical left/right u, and inverted sensor x to near/far canonical v.

constexpr int SDA_PIN = 8;
constexpr int SCL_PIN = 9;
constexpr int SENSOR_WIDTH = 32;
constexpr int SENSOR_HEIGHT = 24;
constexpr int PIXEL_COUNT = SENSOR_WIDTH * SENSOR_HEIGHT;

constexpr float MIN_CONTRAST_C = 4.0f;
constexpr float SEED_MIN_DELTA_C = 3.0f;
constexpr float SEED_CONTRAST_FRACTION = 0.45f;
constexpr float GROW_MIN_DELTA_C = 1.5f;
constexpr float GROW_MAX_DELTA_C = 5.0f;
constexpr float GROW_CONTRAST_FRACTION = 0.20f;
constexpr int MIN_REGION_PIXELS = 3;

constexpr float EMA_ALPHA = 0.35f;
constexpr float DEAD_ZONE_PIXELS = 0.45f;
constexpr int PRESENCE_FRAMES = 3;
constexpr int LOSS_FRAMES = 5;

Adafruit_MLX90640 mlx;
float frame[PIXEL_COUNT];
float medianScratch[PIXEL_COUNT];
bool visited[PIXEL_COUNT];
int16_t regionQueue[PIXEL_COUNT];

bool sourcePresent = false;
bool filterInitialized = false;
int detectionStreak = 0;
int lossStreak = 0;
float pendingXSum = 0.0f;
float pendingYSum = 0.0f;
float smoothedX = 15.5f;
float smoothedY = 11.5f;
float stableX = 15.5f;
float stableY = 11.5f;
float measuredFps = 0.0f;
uint32_t lastFrameMicros = 0;
uint32_t sequenceNumber = 0;

struct Detection {
  bool valid;
  float centroidX;
  float centroidY;
  int area;
  float background;
  float maximum;
  float threshold;
};

int compareFloats(const void* first, const void* second) {
  const float a = *static_cast<const float*>(first);
  const float b = *static_cast<const float*>(second);
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}

float clampFloat(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

bool frameStatistics(float& background, float& maximum, int& maxIndex) {
  int validCount = 0;
  maximum = -INFINITY;
  maxIndex = -1;

  for (int i = 0; i < PIXEL_COUNT; ++i) {
    const float temperature = frame[i];
    if (!isfinite(temperature)) continue;
    medianScratch[validCount++] = temperature;
    if (temperature > maximum) {
      maximum = temperature;
      maxIndex = i;
    }
  }

  if (validCount < PIXEL_COUNT / 2 || maxIndex < 0) return false;
  qsort(medianScratch, validCount, sizeof(float), compareFloats);
  const int middle = validCount / 2;
  background = (validCount % 2 == 0)
                   ? 0.5f * (medianScratch[middle - 1] + medianScratch[middle])
                   : medianScratch[middle];
  return isfinite(background) && isfinite(maximum);
}

Detection detectHotRegion() {
  Detection result = {false, stableX, stableY, 0, NAN, NAN, NAN};
  int maxIndex = -1;
  if (!frameStatistics(result.background, result.maximum, maxIndex)) return result;

  const float contrast = result.maximum - result.background;
  const float seedThreshold = result.background +
      fmaxf(SEED_MIN_DELTA_C, contrast * SEED_CONTRAST_FRACTION);
  const float growDelta = clampFloat(
      contrast * GROW_CONTRAST_FRACTION,
      GROW_MIN_DELTA_C,
      GROW_MAX_DELTA_C);
  result.threshold = result.background + growDelta;

  if (contrast < MIN_CONTRAST_C || result.maximum < seedThreshold) return result;

  memset(visited, 0, sizeof(visited));
  int queueHead = 0;
  int queueTail = 0;
  regionQueue[queueTail++] = static_cast<int16_t>(maxIndex);
  visited[maxIndex] = true;

  float weightedX = 0.0f;
  float weightedY = 0.0f;
  float totalWeight = 0.0f;

  while (queueHead < queueTail) {
    const int index = regionQueue[queueHead++];
    const float temperature = frame[index];
    if (!isfinite(temperature) || temperature < result.threshold) continue;

    const int x = index % SENSOR_WIDTH;
    const int y = index / SENSOR_WIDTH;
    const float weight = clampFloat(
        temperature - result.threshold,
        0.5f,
        5.0f);
    weightedX += static_cast<float>(x) * weight;
    weightedY += static_cast<float>(y) * weight;
    totalWeight += weight;
    ++result.area;

    for (int offsetY = -1; offsetY <= 1; ++offsetY) {
      for (int offsetX = -1; offsetX <= 1; ++offsetX) {
        if (offsetX == 0 && offsetY == 0) continue;
        const int neighborX = x + offsetX;
        const int neighborY = y + offsetY;
        if (neighborX < 0 || neighborX >= SENSOR_WIDTH ||
            neighborY < 0 || neighborY >= SENSOR_HEIGHT) {
          continue;
        }
        const int neighborIndex = neighborY * SENSOR_WIDTH + neighborX;
        if (visited[neighborIndex]) continue;
        visited[neighborIndex] = true;
        if (isfinite(frame[neighborIndex]) && frame[neighborIndex] >= result.threshold) {
          regionQueue[queueTail++] = static_cast<int16_t>(neighborIndex);
        }
      }
    }
  }

  if (result.area < MIN_REGION_PIXELS || totalWeight <= 0.0f) return result;
  result.centroidX = weightedX / totalWeight;
  result.centroidY = weightedY / totalWeight;
  result.valid = isfinite(result.centroidX) && isfinite(result.centroidY);
  return result;
}

void updateStablePosition(const Detection& detection) {
  if (detection.valid) {
    lossStreak = 0;
    if (!sourcePresent) {
      ++detectionStreak;
      pendingXSum += detection.centroidX;
      pendingYSum += detection.centroidY;
      if (detectionStreak >= PRESENCE_FRAMES) {
        sourcePresent = true;
        filterInitialized = true;
        smoothedX = pendingXSum / static_cast<float>(detectionStreak);
        smoothedY = pendingYSum / static_cast<float>(detectionStreak);
        stableX = smoothedX;
        stableY = smoothedY;
      }
      return;
    }

    detectionStreak = PRESENCE_FRAMES;
    if (!filterInitialized) {
      smoothedX = detection.centroidX;
      smoothedY = detection.centroidY;
      stableX = smoothedX;
      stableY = smoothedY;
      filterInitialized = true;
    } else {
      smoothedX += EMA_ALPHA * (detection.centroidX - smoothedX);
      smoothedY += EMA_ALPHA * (detection.centroidY - smoothedY);
      const float deltaX = smoothedX - stableX;
      const float deltaY = smoothedY - stableY;
      if (sqrtf(deltaX * deltaX + deltaY * deltaY) >= DEAD_ZONE_PIXELS) {
        stableX = smoothedX;
        stableY = smoothedY;
      }
    }
    return;
  }

  detectionStreak = 0;
  pendingXSum = 0.0f;
  pendingYSum = 0.0f;
  if (!sourcePresent) return;

  ++lossStreak;
  if (lossStreak >= LOSS_FRAMES) {
    sourcePresent = false;
    filterInitialized = false;
    lossStreak = 0;
  }
}

void updateFps() {
  const uint32_t now = micros();
  if (lastFrameMicros != 0) {
    const uint32_t elapsed = now - lastFrameMicros;
    if (elapsed > 0) {
      const float instantFps = 1000000.0f / static_cast<float>(elapsed);
      measuredFps = (measuredFps <= 0.0f)
                        ? instantFps
                        : measuredFps + 0.20f * (instantFps - measuredFps);
    }
  }
  lastFrameMicros = now;
}

void printState(const Detection& detection) {
  const float u = clampFloat(stableY / 23.0f, 0.0f, 1.0f);
  const float v = clampFloat(1.0f - stableX / 31.0f, 0.0f, 1.0f);

  Serial.print("THERMAL|p=");
  Serial.print(sourcePresent ? 1 : 0);
  Serial.print("|u=");
  Serial.print(u, 4);
  Serial.print("|v=");
  Serial.print(v, 4);
  Serial.print("|cx=");
  Serial.print(stableX, 3);
  Serial.print("|cy=");
  Serial.print(stableY, 3);
  Serial.print("|area=");
  Serial.print(detection.valid ? detection.area : 0);
  Serial.print("|bg=");
  Serial.print(detection.background, 2);
  Serial.print("|max=");
  Serial.print(detection.maximum, 2);
  Serial.print("|thr=");
  Serial.print(detection.threshold, 2);
  Serial.print("|fps=");
  Serial.print(measuredFps, 1);
  Serial.print("|seq=");
  Serial.println(sequenceNumber);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  Serial.println("THERMAL_BOOT|status=starting");
  if (!mlx.begin(MLX90640_I2CADDR_DEFAULT, &Wire)) {
    Serial.println("THERMAL_ERROR|sensor=not_found");
    while (true) delay(100);
  }

  mlx.setMode(MLX90640_CHESS);
  mlx.setResolution(MLX90640_ADC_18BIT);
  mlx.setRefreshRate(MLX90640_8_HZ);
  Serial.println("THERMAL_BOOT|status=ready|rate=8|baud=115200");
}

void loop() {
  if (mlx.getFrame(frame) != 0) {
    Serial.println("THERMAL_ERROR|read_frame=1");
    return;
  }

  ++sequenceNumber;
  updateFps();
  const Detection detection = detectHotRegion();
  updateStablePosition(detection);
  printState(detection);
}

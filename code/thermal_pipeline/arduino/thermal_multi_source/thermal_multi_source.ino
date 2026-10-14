#include <Wire.h>
#include <Adafruit_MLX90640.h>
#include <esp_system.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Multi-source thermal tracking MVP for up to eight independent hot regions.
// Raw centroid x/y remain sensor coordinates. The fixed mounting maps sensor
// y to canonical left/right u, and inverted sensor x to near/far canonical v.

constexpr int SDA_PIN = 8;
constexpr int SCL_PIN = 9;
constexpr int SENSOR_WIDTH = 32;
constexpr int SENSOR_HEIGHT = 24;
constexpr int PIXEL_COUNT = SENSOR_WIDTH * SENSOR_HEIGHT;

struct TrackerConfig {
  int maxCandles;
  int maxComponents;
  float minContrastC;
  float seedMinDeltaC;
  float seedContrastFraction;
  float growMinDeltaC;
  float growMaxDeltaC;
  float growContrastFraction;
  int minRegionPixels;
  float matchMaxDistancePixels;
  float emaAlpha;
  float deadZonePixels;
  int presenceFrames;
  int lossFrames;
};

constexpr int MAX_CANDLES = 8;
constexpr int MAX_COMPONENTS = 24;
constexpr TrackerConfig CONFIG = {
    MAX_CANDLES,
    MAX_COMPONENTS,
    4.0f,   // minContrastC
    3.0f,   // seedMinDeltaC
    0.45f,  // seedContrastFraction
    1.5f,   // growMinDeltaC
    5.0f,   // growMaxDeltaC
    0.20f,  // growContrastFraction
    3,      // minRegionPixels
    3.0f,   // matchMaxDistancePixels
    0.35f,  // emaAlpha
    0.45f,  // deadZonePixels
    3,      // presenceFrames
    5       // lossFrames
};

struct Detection {
  float centroidX;
  float centroidY;
  int area;
  float peak;
};

struct Track {
  bool occupied;
  bool confirmed;
  bool seen;
  uint32_t id;
  int hitFrames;
  int missFrames;
  float measuredX;
  float measuredY;
  float smoothedX;
  float smoothedY;
  float stableX;
  float stableY;
  int area;
  float peak;
};

Adafruit_MLX90640 mlx;
float frame[PIXEL_COUNT];
float medianScratch[PIXEL_COUNT];
bool visited[PIXEL_COUNT];
int16_t regionQueue[PIXEL_COUNT];
Detection detections[MAX_COMPONENTS];
Track tracks[MAX_CANDLES];

uint32_t sessionId = 0;
uint32_t sequenceNumber = 0;
uint32_t nextTrackId = 1;
uint32_t lastFrameMicros = 0;
float measuredFps = 0.0f;

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

bool frameStatistics(float& background, float& maximum) {
  int validCount = 0;
  maximum = -INFINITY;
  for (int index = 0; index < PIXEL_COUNT; ++index) {
    const float temperature = frame[index];
    if (!isfinite(temperature)) continue;
    medianScratch[validCount++] = temperature;
    if (temperature > maximum) maximum = temperature;
  }
  if (validCount < PIXEL_COUNT / 2 || !isfinite(maximum)) return false;
  qsort(medianScratch, validCount, sizeof(float), compareFloats);
  const int middle = validCount / 2;
  background = (validCount % 2 == 0)
                   ? 0.5f * (medianScratch[middle - 1] + medianScratch[middle])
                   : medianScratch[middle];
  return isfinite(background);
}

void retainDetection(const Detection& detection, int& detectionCount) {
  if (detectionCount < CONFIG.maxComponents) {
    detections[detectionCount++] = detection;
    return;
  }

  int weakest = 0;
  for (int index = 1; index < detectionCount; ++index) {
    if (detections[index].peak < detections[weakest].peak) weakest = index;
  }
  if (detection.peak > detections[weakest].peak) detections[weakest] = detection;
}

int detectHotRegions(float& background, float& maximum, float& threshold) {
  if (!frameStatistics(background, maximum)) {
    background = NAN;
    maximum = NAN;
    threshold = NAN;
    return 0;
  }

  const float frameContrast = maximum - background;
  const float growDelta = clampFloat(
      frameContrast * CONFIG.growContrastFraction,
      CONFIG.growMinDeltaC,
      CONFIG.growMaxDeltaC);
  threshold = background + growDelta;
  if (frameContrast < CONFIG.minContrastC) return 0;

  memset(visited, 0, sizeof(visited));
  int detectionCount = 0;

  for (int start = 0; start < PIXEL_COUNT; ++start) {
    if (visited[start]) continue;
    visited[start] = true;
    if (!isfinite(frame[start]) || frame[start] < threshold) continue;

    int queueHead = 0;
    int queueTail = 0;
    regionQueue[queueTail++] = static_cast<int16_t>(start);
    float weightedX = 0.0f;
    float weightedY = 0.0f;
    float totalWeight = 0.0f;
    float peak = -INFINITY;
    int area = 0;

    while (queueHead < queueTail) {
      const int index = regionQueue[queueHead++];
      const float temperature = frame[index];
      const int x = index % SENSOR_WIDTH;
      const int y = index / SENSOR_WIDTH;
      const float weight = clampFloat(temperature - threshold, 0.5f, 5.0f);
      weightedX += static_cast<float>(x) * weight;
      weightedY += static_cast<float>(y) * weight;
      totalWeight += weight;
      if (temperature > peak) peak = temperature;
      ++area;

      for (int offsetY = -1; offsetY <= 1; ++offsetY) {
        for (int offsetX = -1; offsetX <= 1; ++offsetX) {
          if (offsetX == 0 && offsetY == 0) continue;
          const int neighborX = x + offsetX;
          const int neighborY = y + offsetY;
          if (neighborX < 0 || neighborX >= SENSOR_WIDTH ||
              neighborY < 0 || neighborY >= SENSOR_HEIGHT) {
            continue;
          }
          const int neighbor = neighborY * SENSOR_WIDTH + neighborX;
          if (visited[neighbor]) continue;
          visited[neighbor] = true;
          if (isfinite(frame[neighbor]) && frame[neighbor] >= threshold) {
            regionQueue[queueTail++] = static_cast<int16_t>(neighbor);
          }
        }
      }
    }

    const float regionContrast = peak - background;
    const float seedThreshold = background + fmaxf(
        CONFIG.seedMinDeltaC,
        regionContrast * CONFIG.seedContrastFraction);
    if (area < CONFIG.minRegionPixels || totalWeight <= 0.0f ||
        regionContrast < CONFIG.minContrastC || peak < seedThreshold) {
      continue;
    }

    Detection detection = {
        weightedX / totalWeight,
        weightedY / totalWeight,
        area,
        peak
    };
    if (isfinite(detection.centroidX) && isfinite(detection.centroidY)) {
      retainDetection(detection, detectionCount);
    }
  }
  return detectionCount;
}

float squaredDistance(const Track& track, const Detection& detection) {
  const float deltaX = track.measuredX - detection.centroidX;
  const float deltaY = track.measuredY - detection.centroidY;
  return deltaX * deltaX + deltaY * deltaY;
}

uint32_t allocateTrackId() {
  uint32_t allocated = nextTrackId++;
  if (allocated == 0) allocated = nextTrackId++;
  return allocated;
}

void updateMatchedTrack(Track& track, const Detection& detection) {
  track.seen = true;
  track.missFrames = 0;
  track.measuredX = detection.centroidX;
  track.measuredY = detection.centroidY;
  track.area = detection.area;
  track.peak = detection.peak;

  if (!track.confirmed) ++track.hitFrames;
  track.smoothedX += CONFIG.emaAlpha * (detection.centroidX - track.smoothedX);
  track.smoothedY += CONFIG.emaAlpha * (detection.centroidY - track.smoothedY);
  const float deltaX = track.smoothedX - track.stableX;
  const float deltaY = track.smoothedY - track.stableY;
  if (sqrtf(deltaX * deltaX + deltaY * deltaY) >= CONFIG.deadZonePixels) {
    track.stableX = track.smoothedX;
    track.stableY = track.smoothedY;
  }

  if (!track.confirmed && track.hitFrames >= CONFIG.presenceFrames) {
    track.confirmed = true;
    track.id = allocateTrackId();
  }
}

void matchTracks(const bool confirmedPass, const int detectionCount,
                 bool detectionAssigned[MAX_COMPONENTS],
                 bool trackAssigned[MAX_CANDLES]) {
  const float gateSquared = CONFIG.matchMaxDistancePixels *
                            CONFIG.matchMaxDistancePixels;
  while (true) {
    int bestTrack = -1;
    int bestDetection = -1;
    float bestDistance = gateSquared + 1.0f;
    for (int trackIndex = 0; trackIndex < CONFIG.maxCandles; ++trackIndex) {
      const Track& track = tracks[trackIndex];
      if (!track.occupied || track.confirmed != confirmedPass ||
          trackAssigned[trackIndex]) {
        continue;
      }
      for (int detectionIndex = 0; detectionIndex < detectionCount;
           ++detectionIndex) {
        if (detectionAssigned[detectionIndex]) continue;
        const float distance = squaredDistance(track, detections[detectionIndex]);
        if (distance <= gateSquared && distance < bestDistance) {
          bestDistance = distance;
          bestTrack = trackIndex;
          bestDetection = detectionIndex;
        }
      }
    }
    if (bestTrack < 0) return;
    updateMatchedTrack(tracks[bestTrack], detections[bestDetection]);
    trackAssigned[bestTrack] = true;
    detectionAssigned[bestDetection] = true;
  }
}

int freeTrackSlot() {
  for (int index = 0; index < CONFIG.maxCandles; ++index) {
    if (!tracks[index].occupied) return index;
  }
  return -1;
}

void startTentativeTrack(const int slot, const Detection& detection) {
  Track& track = tracks[slot];
  memset(&track, 0, sizeof(track));
  track.occupied = true;
  track.seen = true;
  track.hitFrames = 1;
  track.measuredX = detection.centroidX;
  track.measuredY = detection.centroidY;
  track.smoothedX = detection.centroidX;
  track.smoothedY = detection.centroidY;
  track.stableX = detection.centroidX;
  track.stableY = detection.centroidY;
  track.area = detection.area;
  track.peak = detection.peak;
  if (CONFIG.presenceFrames <= 1) {
    track.confirmed = true;
    track.id = allocateTrackId();
  }
}

void updateTracks(const int detectionCount) {
  bool detectionAssigned[MAX_COMPONENTS] = {false};
  bool trackAssigned[MAX_CANDLES] = {false};
  for (int index = 0; index < CONFIG.maxCandles; ++index) {
    if (tracks[index].occupied) tracks[index].seen = false;
  }

  // Confirmed tracks get first claim, which reduces ID churn near tentative blobs.
  matchTracks(true, detectionCount, detectionAssigned, trackAssigned);
  matchTracks(false, detectionCount, detectionAssigned, trackAssigned);

  for (int index = 0; index < CONFIG.maxCandles; ++index) {
    Track& track = tracks[index];
    if (!track.occupied || trackAssigned[index]) continue;
    if (!track.confirmed) {
      memset(&track, 0, sizeof(track));
      continue;
    }
    ++track.missFrames;
    if (track.missFrames >= CONFIG.lossFrames) {
      memset(&track, 0, sizeof(track));
    }
  }

  // Fill free capacity with the strongest unmatched components first.
  while (true) {
    const int slot = freeTrackSlot();
    if (slot < 0) break;
    int strongest = -1;
    for (int index = 0; index < detectionCount; ++index) {
      if (detectionAssigned[index]) continue;
      if (strongest < 0 || detections[index].peak > detections[strongest].peak) {
        strongest = index;
      }
    }
    if (strongest < 0) break;
    startTentativeTrack(slot, detections[strongest]);
    detectionAssigned[strongest] = true;
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

int confirmedTrackCount() {
  int count = 0;
  for (int index = 0; index < CONFIG.maxCandles; ++index) {
    if (tracks[index].occupied && tracks[index].confirmed) ++count;
  }
  return count;
}

void printSnapshot(const float background, const float threshold) {
  Serial.print("THERMAL2|session=");
  Serial.print(sessionId);
  Serial.print("|seq=");
  Serial.print(sequenceNumber);
  Serial.print("|count=");
  Serial.print(confirmedTrackCount());
  Serial.print("|bg=");
  Serial.print(background, 2);
  Serial.print("|thr=");
  Serial.print(threshold, 2);
  Serial.print("|fps=");
  Serial.print(measuredFps, 1);
  Serial.print("|sources=");

  bool first = true;
  for (int index = 0; index < CONFIG.maxCandles; ++index) {
    const Track& track = tracks[index];
    if (!track.occupied || !track.confirmed) continue;
    if (!first) Serial.print(';');
    first = false;
    const float u = clampFloat(track.stableY / 23.0f, 0.0f, 1.0f);
    const float v = clampFloat(1.0f - track.stableX / 31.0f, 0.0f, 1.0f);
    Serial.print(track.id);
    Serial.print(',');
    Serial.print(u, 4);
    Serial.print(',');
    Serial.print(v, 4);
    Serial.print(',');
    Serial.print(track.stableX, 3);
    Serial.print(',');
    Serial.print(track.stableY, 3);
    Serial.print(',');
    Serial.print(track.area);
    Serial.print(',');
    Serial.print(track.peak, 2);
    Serial.print(',');
    Serial.print(track.seen ? 1 : 0);
    Serial.print(',');
    Serial.print(track.missFrames);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  sessionId = esp_random();
  if (sessionId == 0) sessionId = 1;
  memset(tracks, 0, sizeof(tracks));

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  Serial.println("THERMAL2_BOOT|status=starting");
  if (!mlx.begin(MLX90640_I2CADDR_DEFAULT, &Wire)) {
    Serial.println("THERMAL2_ERROR|sensor=not_found");
    while (true) delay(100);
  }

  mlx.setMode(MLX90640_CHESS);
  mlx.setResolution(MLX90640_ADC_18BIT);
  mlx.setRefreshRate(MLX90640_8_HZ);
  Serial.print("THERMAL2_BOOT|status=ready|session=");
  Serial.print(sessionId);
  Serial.print("|rate=8|baud=115200|max=");
  Serial.println(CONFIG.maxCandles);
}

void loop() {
  if (mlx.getFrame(frame) != 0) {
    Serial.println("THERMAL2_ERROR|read_frame=1");
    return;
  }

  ++sequenceNumber;
  updateFps();
  float background = NAN;
  float maximum = NAN;
  float threshold = NAN;
  const int detectionCount = detectHotRegions(background, maximum, threshold);
  updateTracks(detectionCount);
  printSnapshot(background, threshold);
}

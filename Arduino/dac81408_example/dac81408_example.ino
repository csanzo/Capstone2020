#include <DAC81408.h>

#define slavePin 4

DAC81408 DAC;

void setup() {
  Serial.begin(9600);
  Serial.println("DAC81408 example");
  
  // Initialize DAC and set 1.0V on channel 0
  DAC.init(slavePin);
  DAC.set(0, 1);

  Serial.println("Finished");
}

void loop() {
}

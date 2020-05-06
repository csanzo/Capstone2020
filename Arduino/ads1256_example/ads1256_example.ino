#include <ADS1256.h>

#define CS 10
#define DRDY 11
#define RST 12
#define PDWN 13

ADS1256 ADC1256;

bool retval;

void setup() {
  Serial.begin(9600);
  Serial.println("ADS1256 example");

  retval = ADC1256.init(CS, RST, PDWN, DRDY);
}

void loop() {
  if (retval) {
    // Read channel 0 of ADC
    Serial.println(ADC1256.read(0), 6);
  } else {
    Serial.println("Retrying ADC init...");
    retval = ADC1256.init(CS, RST, PDWN, DRDY);
  }
}

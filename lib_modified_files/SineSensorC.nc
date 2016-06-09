/* $Id: SineSensorC.nc,v 1.4 2006-12-12 18:23:47 vlahan Exp $
 * Copyright (c) 2006 Intel Corporation
 * All rights reserved.
 *
 * This file is distributed under the terms in the attached INTEL-LICENSE     
 * file. If you do not find these files, copies can be found by writing to
 * Intel Research Berkeley, 2150 Shattuck Avenue, Suite 1300, Berkeley, CA, 
 * 94704.  Attention:  Intel License Inquiry.
 */
/**
 * The micaZ doesn't have any built-in sensors - the DemoSensor returns
 * a constant value of 0xbeef, or just reads the ground value for the
 * stream sensor.
 *
 * @author Philip Levis
 * @authod David Gay
 */

/*
 * To be placed at tos/system/
 */

#include <stdlib.h> 
#include <string.h> 

generic module SineSensorC()
{
  provides interface Init;
  provides interface Read<uint16_t>;
}
implementation {

  uint32_t counter;
  uint16_t current_node;

  command error_t Init.init() {
    counter = TOS_NODE_ID * 40;
    return SUCCESS;
  }

  float getTime(){
    char * string_time = sim_time_string();
    float time, seconds;
    uint16_t hours, minutes;
    hours = atoi(strtok(string_time, ":"));
    minutes = atoi(strtok(NULL, ":"));
    seconds = atof(strtok(NULL, ":"));
    time = hours * 3600 + minutes * 60 + seconds;
    //dbg("Report", "time : %s - and time parsed : %hu\n", string_time, (int)time);

    return time; 
  }
  
  task void readTask() {
    float time = getTime();
    float val;//= (float)counter;
    //val = val / 20.0;
    val = sin((time/5) + current_node) * 32768.0;
    val += 32768.0;
    //counter++;
    signal Read.readDone(SUCCESS, (uint16_t)val);
  }
  command error_t Read.read(uint16_t node_nb) {
    current_node = node_nb;
    post readTask();
    return SUCCESS;
  }
}

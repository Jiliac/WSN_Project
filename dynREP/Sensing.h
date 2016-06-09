/*
 * Copyright (c) 2006 Intel Corporation
 * All rights reserved.
 *
 * This file is distributed under the terms in the attached INTEL-LICENSE     
 * file. If you do not find these files, copies can be found by writing to
 * Intel Research Berkeley, 2150 Shattuck Avenue, Suite 1300, Berkeley, CA, 
 * 94704.  Attention:  Intel License Inquiry.
 */

// @author David Gay

#ifndef SENSING_H
#define SENSING_H

enum {
  /* Number of readings per message. If you increase this, you may have to
     increase the message_t size. */
  NREADINGS = 9,

  /* Default sampling period. */
  DEFAULT_INTERVAL = 256,

  AM_SENSING = 0x93
};

typedef nx_struct sensing {
  //nx_uint16_t version; /* Version of the interval. */
  nx_uint16_t interval; /* Sampling period. */
  nx_uint16_t id; /* Mote id of sending mote. */
  //nx_uint16_t count; /* The readings are samples count * NREADINGS onwards */
  nx_uint16_t readings[NREADINGS];
} sensing_t;

typedef nx_struct update {
  nx_uint16_t id; /* Mote id of sending mote. */
  nx_uint16_t readings[2];
} update_t;

typedef nx_struct control {
    nx_uint16_t id;
    nx_uint16_t receiver_id;
    nx_uint8_t type; // types on the last bits: 00000.ack.join.leave
} control_t;

#endif

* CMOS Inverter Timing Characterization Netlist
.param VDD_VAL = 1.0
.param SLEW_IN = 20p
.param C_LOAD  = 5f
.param TEMP_C  = 25

.temp {TEMP_C}

.model NMOS_MOD nmos level=1 vto=0.35 kp=250u lambda=0.05
.model PMOS_MOD pmos level=1 vto=-0.35 kp=110u lambda=0.05

Vdd vdd 0 DC {VDD_VAL}
Vin in 0 PULSE(0 {VDD_VAL} 100p {SLEW_IN} {SLEW_IN} 500p 1.2n)

Mp out in vdd vdd PMOS_MOD W=1.0u L=0.1u
Mn out in 0   0   NMOS_MOD W=0.45u L=0.1u

Cload out 0 {C_LOAD}

.tran 1p 1.2n

.meas tran tpHL TRIG v(in) VAL={0.5*VDD_VAL} RISE=1 TARG v(out) VAL={0.5*VDD_VAL} FALL=1
.meas tran tpLH TRIG v(in) VAL={0.5*VDD_VAL} FALL=1 TARG v(out) VAL={0.5*VDD_VAL} RISE=1
.meas tran fall_slew TRIG v(out) VAL={0.8*VDD_VAL} FALL=1 TARG v(out) VAL={0.2*VDD_VAL} FALL=1
.meas tran rise_slew TRIG v(out) VAL={0.2*VDD_VAL} RISE=1 TARG v(out) VAL={0.8*VDD_VAL} RISE=1

.end
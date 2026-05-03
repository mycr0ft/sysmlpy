package PortionUsage_Invalid {	
	part p1 {
		snapshot s1;
		timeslice t1 {
			snapshot s2;
		}
	}
	
	// XPECT errors -->"Must be owned by an occurrence definition or usage." at "snapshot s2;"
	snapshot s2;
	// XPECT errors -->"Must be owned by an occurrence definition or usage." at "timeslice t2;"	
	timeslice t2;
}

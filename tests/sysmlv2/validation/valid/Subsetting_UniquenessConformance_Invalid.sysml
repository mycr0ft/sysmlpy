package '1a-Parts Tree Simplified' {
	
	part rearAxleAssembly {			
		part rearWheel: Wheel[2];
		// XPECT errors --> "Subsetting/redefining feature cannot be nonunique if subsetted/redefined feature is unique" at "rearWheel"
		part rearWheel_1: Wheel[2] nonunique subsets rearWheel;
		// XPECT errors --> "Subsetting/redefining feature cannot be nonunique if subsetted/redefined feature is unique" at "rearWheel"
		part rearWheel_2[0..1] nonunique subsets rearWheel;
	}
	part def Wheel;
}


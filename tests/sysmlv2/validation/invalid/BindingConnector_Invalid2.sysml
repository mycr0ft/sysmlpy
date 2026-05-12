package '1a-Parts Tree Simplified' {
	
	part rearAxleAssembly {			
		part rearWheel: Wheel[2];
		// XPECT warnings --> "Bound features should have conforming types" at "rearWheel+1"
		ref x = rearWheel+1;
	}
	part def Wheel;
}

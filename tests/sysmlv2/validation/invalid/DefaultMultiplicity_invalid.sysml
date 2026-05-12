package DefaultMultiplicity {

	attribute a1;
	item i1;
	part p1;
	port t1;
	
	part def P {
		// These kinds of usages have default multiplicity of [1..1].
		attribute a2 :> a1;
		item i2 :> i1;
		part p2 :> p1;
		port t2 :> t1;
		
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "a2"
		attribute a3[*] :> a2;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "i2"
		item i3[*] :> i2;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "p2"
		part p3[*] :> p2;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "t2"
		port t3[*] :> t2;
		
		attribute a4;
		item i4;
		part p4;
		port t4;
		
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "a4"
		attribute a5[*] :> a4;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "i4"
		item i5[*] :> i4;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "p4"
		part p5[*] :> p4;
		// XPECT warnings ---> "Subsetting/redefining feature should not have larger multiplicity upper bound" at "t4"
		port t5[*] :> t4;		
	}
	
	part def Q {
		// These kinds of usages do not have default multiplicity.
		action n1;
		state s1;
		
		action n2[*] :> n1;
		state s2[*] :> s1;
	}
	
}

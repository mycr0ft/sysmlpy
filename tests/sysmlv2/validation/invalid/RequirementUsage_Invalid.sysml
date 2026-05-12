package 'Requirement Definitions' {
	
	part def A {
		part a;
	}
	constraint def Rdef;
	constraint c: Rdef;
	requirement def <'1'> R1def;
	requirement def <'11'> R11def;
	requirement def <'2'> R2def  :> Rdef;
	
	//XPECT errors --> "A requirement must be typed by one requirement definition." at "requirement <'1.0'> r10 : R1def, R11def;"
	requirement <'1.0'> r10 : R1def, R11def;
	/* XPECT errors ---
		"A requirement  must be typed by one requirement definition." at "requirement <'1.1'> r11 : Rdef;"
	--- */
	requirement <'1.1'> r11 : Rdef;
	//XPECT errors --> "A requirement must be typed by one requirement definition." at "requirement <'1.2'> r12 : R1def, R2def;"
	requirement <'1.2'> r12 : R1def, R2def;
	//*XPECT errors ---
		"A requirement must be typed by one requirement definition." at "requirement r13 : A;"
	---*/
	// XPECT warnings --> "Duplicate of inherited member name 'self' from Part, RequirementCheck" at "requirement r13 : A;"
	requirement r13 : A;
	//*XPECT errors ---
		"A requirement must be typed by one requirement definition." at "requirement r14 : A::a;"
	---*/
	// XPECT warnings --> "Duplicate of inherited member name 'self' from Part, RequirementCheck" at "requirement r14 : A::a;"
	requirement r14 : A::a;
	//*XPECT errors ---
		"A requirement must be typed by one requirement definition." at "requirement r15 : c;"
	---*/
	requirement r15 : c;
}
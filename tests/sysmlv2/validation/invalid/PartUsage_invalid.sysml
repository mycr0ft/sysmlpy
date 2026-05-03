package pkg {
	public import ScalarValues::*;
	part def A {
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p1: Real;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "part p1: Real;"
		part p1: Real;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p2: att;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "part p2: att;"
		part p2: att;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p3: act;"
		//* XPECT warnings ---
		 "Duplicate of inherited member name 'self' from Action, Part" at "part p3: act;"
		 "Duplicate of inherited member name 'start' from Action, Part" at "part p3: act;"
		 "Duplicate of inherited member name 'done' from Action, Part" at "part p3: act;"
		--- */
		part p3: act;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p4: AttDef;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "part p4: AttDef;"
		part p4: AttDef;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p5: PartDef::aPort;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from Part, Port" at "part p5: PartDef::aPort;"
		part p5: PartDef::aPort;
		// XPECT errors ---> "An occurrence, item or part must be typed by occurrence definitions." at "part p6: PartDef::aPart;"
		part p6: PartDef::aPart;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "part p7: PartDef, AttDef;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "part p7: PartDef, AttDef;"
		part p7: PartDef, AttDef;
	}
	attribute def AttDef;
	attribute att: AttDef;
	part def PartDef {
		port aPort;
		part aPart;
	}
	action act;
}

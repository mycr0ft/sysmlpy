package pkg {
	public import ScalarValues::*;
	item def A {
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "item i1: Real;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Item" at "item i1: Real;"
		item i1: Real;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "item i2: att;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Item" at "item i2: att;"
		item i2: att;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "item i3: act;"
		//* XPECT warnings ---
		   "Duplicate of inherited member name 'self' from Action, Item" at "item i3: act;"
		   "Duplicate of inherited member name 'start' from Action, Item" at "item i3: act;"
		   "Duplicate of inherited member name 'done' from Action, Item" at "item i3: act;"
		--- */
		item i3: act;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "item i4: AttDef;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Item" at "item i4: AttDef;"
		item i4: AttDef;
		// XPECT errors ---> "An occurrence, item or part must be typed by occurrence definitions." at "item i5: PartDef::aPort;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from Item, Port" at "item i5: PartDef::aPort;"
		item i5: PartDef::aPort;
		// XPECT errors ---> "An occurrence, item or part must be typed by occurrence definitions." at "item i6: PartDef::aPart;"
		item i6: PartDef::aPart;
		// XPECT errors --> "An occurrence, item or part must be typed by occurrence definitions." at "item i7: PartDef, AttDef;"
		// XPECT warnings --> "Duplicate of inherited member name 'self' from DataValue, Part" at "item i7: PartDef, AttDef;"
		item i7: PartDef, AttDef;
	}
	attribute def AttDef;
	attribute att: AttDef;
	part def PartDef {
		port aPort;
		part aPart;
	}
	action act;
}
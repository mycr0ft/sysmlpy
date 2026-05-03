package pkg {
	part def A {
		part b: B;
		part c: B;
	}
	part def B {}
	part a : A {
		//XPECT warnings --> "Duplicate of inherited member name 'b' from A" at "b"
		part b: B;
		part redefines c;
	}
}

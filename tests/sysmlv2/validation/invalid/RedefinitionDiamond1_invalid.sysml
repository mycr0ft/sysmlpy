package RedefinitionDiamond {
	part A {
		part p[*];
	}
	part A1 :> A {
		p1 :>> p;
	}
	part A2 :> A {
		p :>> p; // 1
	}
	
	part B :> A1, A2 {
		p2 :>> p1; // 2
// XPECT warnings ---> "Duplicate of inherited member name 'p' from A2" at "p"
		part p;
	}
}
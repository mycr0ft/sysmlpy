package Q {
  part def F {
  	part a : A;
  }
  
  part f : F;
  
  part def A {
    // XPECT errors --> "Must be an accessible feature (use dot notation for nesting)" at "f::a"
    part g = f::a;
  }
  
  part def B {
  	part f : F;
  	part a : A;
  }
  
  part def C {
  	part b : B;
  
	part c subsets b.f {
	  	part aa subsets a;
	}
	
    // XPECT errors --> "Must be an accessible feature (use dot notation for nesting)" at "c::aa"
	connect b.f.a to c::aa;
  }
	
}

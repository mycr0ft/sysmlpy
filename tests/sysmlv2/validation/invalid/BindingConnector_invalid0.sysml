package BindingConnector_Invalid {
	part def A1;
	part def A2;
	part b {				
		part b1 {
			out ref a : A1;
		}
		bind b1.a = b2.a1;
		// XPECT warnings --> "Bound features should have conforming types" at "bind b1.a = b2.a2;"
		bind b1.a = b2.a2;
		
		part b2 {
			in ref a1: A1;		
			in ref a2 : A2;		
		}
		
	}
}

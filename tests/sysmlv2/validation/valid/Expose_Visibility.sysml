// XPECT noErrors ---> ""
package ExposeVisibility {
	part def A;
	
	view v1 {
		expose A;
	}
	
	view v2 :> v1 {
		part a : A;
	}
}

package Verification_invalid {

	requirement def R {
		doc /* ... */
		
		// XPECT errors --> "A requirement verification must be in the objective of a verification case." at "verify requirement : R;"		
		verify requirement : R;

		// XPECT errors --> "A requirement verification must be in the objective of a verification case." at "verify r;"		
		verify r;
	}
	
	requirement r : R;

	verification def VerificationCase {		
		objective {
			verify requirement : R;
		}
		
		requirement {
			// XPECT errors --> "A requirement verification must be in the objective of a verification case." at "verify r;"		
			verify r;
		}
	}
	
	case def VerificationPlan {
		objective {
			// XPECT errors --> "A requirement verification must be in the objective of a verification case." at "verify r;"		
			verify r;
		}
	}
	
}
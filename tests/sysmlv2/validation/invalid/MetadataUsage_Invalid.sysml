package Test {
	
	metadata def A {
		ref :>> annotatedElement : SysML::AttributeUsage;
		attribute x : ScalarValues::Integer;
		attribute y : ScalarValues::String;
		attribute z : ScalarValues::Boolean;
		attribute u {
			attribute v : ScalarValues::Integer;
		}
	}
	
	calc def f { in x : ScalarValues::Boolean; }
	
	// XPECT errors --> "Must be model-level evaluable" at "filter f((as A).z);"
	filter f((as A).z);
	// XPECT errors --> "Must be model-level evaluable" at "filter ~(as A).z;"
	filter ~(as A).z;
	// XPECT errors --> "Must be model-level evaluable" at "filter (as A).y->ControlFunctions::collect {in ref x; x};"
	filter (as A).y->ControlFunctions::collect {in ref x; x};
	// XPECT errors --> "Must have a Boolean result" at "filter new A(null, 1, "", false);"
	filter new A(null, 1, "", false);
	
	enum def E :> ScalarValues::String {
		enum e = "e";
	}
	
	attribute bad;
	
	attribute a {
		@A {
			// XPECT errors --> "Must be model-level evaluable" at "= ~3"
			x = ~3;
			y = E::e;
			// XPECT errors --> "Must be model-level evaluable" at "= f((as A).z)"
			z = f((as A).z);
			u {
				v = 1;
				// XPECT errors --> "Must redefine an owning-type feature" at "bad;"
				bad;
			}		
		}
	}
	
	item p {
		// XPECT errors --> "Cannot annotate ItemUsage" at "@A;"
		@A;
		// XPECT errors --> "Must have a concrete type" at "@Metaobjects::Metaobject;"
		@Metaobjects::Metaobject;
	}
	
}

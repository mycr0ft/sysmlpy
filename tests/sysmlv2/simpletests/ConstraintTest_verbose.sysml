// XPECT noErrors ---> ""
package ConstraintTest {
	public import ISQ::MassValue;
	public import SI::kg;
	public import NumericalFunctions::sum;
	
	constraint def MassAnalysis {
		attribute totalMass: MassValue;
		attribute componentMasses: MassValue[0..*];		

		totalMass == sum(componentMasses)
	}
	
	part def Component {
		attribute mass: MassValue;
	}
	
	part vehicle : Component {	
		part engine : Component;
		part frontAxleAssembly : Component;
		part rearAxleAssembly : Component;	
	}
	part vehicle1a :> vehicle {
		assert constraint massAnalysis : MassAnalysis {
			attribute totalMass redefines MassAnalysis::totalMass;
			attribute componentMasses redefines MassAnalysis::componentMasses;
		}
		attribute mass redefines vehicle::mass;
		part engine redefines vehicle::engine {
			attribute mass redefines vehicle::engine::mass;
		}
		part frontAxleAssembly redefines vehicle::frontAxleAssembly {
			attribute mass redefines vehicle::frontAxleAssembly::mass;
		}
		part rearAxleAssembly redefines vehicle::rearAxleAssembly {
			attribute mass redefines vehicle::rearAxleAssembly::mass;
		}
		
		bind massAnalysis.totalMass = mass;
		bind massAnalysis.componentMasses = engine.mass;
		bind massAnalysis.componentMasses = frontAxleAssembly.mass;
		bind massAnalysis.componentMasses = rearAxleAssembly.mass;
	}
	part vehicle1b :> vehicle {
		assert constraint massAnalysis : MassAnalysis {
			attribute totalMass redefines totalMass = mass;
			attribute componentMasses redefines MassAnalysis::componentMasses = (engine.mass, frontAxleAssembly.mass, rearAxleAssembly.mass);		
		}	
		attribute mass redefines vehicle::mass;
		part engine redefines engine {
			attribute mass redefines mass;
		}
		part frontAxleAssembly redefines frontAxleAssembly {
			attribute mass redefines mass;
		}
		part rearAxleAssembly redefines rearAxleAssembly {
			attribute mass redefines mass;
		}
		
	}
		
	constraint def MassAnalysis2 { 
		in totalMass : MassValue;
		in componentMasses: MassValue[0..*];
		
		totalMass == sum(componentMasses)
	}
	
	part vehicle2a :> vehicle {
		assert constraint massConstraint : MassAnalysis2;
		
		attribute mass redefines mass;
		part engine redefines engine {
			attribute mass redefines mass;
		}
		part frontAxleAssembly redefines frontAxleAssembly {
			attribute mass redefines mass;
		}
		part rearAxleAssembly redefines rearAxleAssembly {
			attribute mass redefines mass;
		}
		
		bind massConstraint.totalMass = mass;
		bind massConstraint.componentMasses = engine.mass;
		bind massConstraint.componentMasses = frontAxleAssembly.mass;
		bind massConstraint.componentMasses = rearAxleAssembly.mass;
	}
		
	part vehicle2b :> vehicle {
		assert constraint massAnalysis2 : MassAnalysis2 {
			in totalMass = mass;
			in componentMasses = (engine.mass, frontAxleAssembly.mass, rearAxleAssembly.mass);
		}
		attribute mass redefines mass;
		part engine redefines engine {
			attribute mass redefines mass;
		}
		part frontAxleAssembly redefines frontAxleAssembly {
			attribute mass redefines mass;
		}
		part rearAxleAssembly redefines rearAxleAssembly {
			attribute mass redefines mass;
		}
	}
	
	constraint def MassAnalysis3 {
		in totalMass : MassValue;
		in componentMasses: MassValue[0..*];
	}
	
	constraint massAnalysis3 : MassAnalysis3 {
		in totalMass : MassValue;
		in componentMasses: MassValue[0..*];
		
		totalMass == sum(componentMasses)
	}
	
	part vehicle3 :> vehicle {
		assert massAnalysis3 {
			in totalMass = mass;
			in componentMasses = (engine.mass, frontAxleAssembly.mass, rearAxleAssembly.mass);
		}
		attribute mass redefines mass;
		part engine redefines engine {
			attribute mass redefines mass;
		}
		part frontAxleAssembly redefines frontAxleAssembly {
			attribute mass redefines mass;
		}
		part rearAxleAssembly redefines rearAxleAssembly {
			attribute mass redefines mass;
		}
	}
	
	part vehicle4 :> vehicle {
		assert constraint { mass == engine.mass + frontAxleAssembly.mass + rearAxleAssembly.mass }
		attribute mass redefines mass;
		part engine redefines engine {
			attribute mass redefines mass;
		}
		part frontAxleAssembly redefines frontAxleAssembly {
			attribute mass redefines mass;
		}
		part rearAxleAssembly redefines vehicle::rearAxleAssembly {
			attribute mass redefines mass;
		}
	}
	
}
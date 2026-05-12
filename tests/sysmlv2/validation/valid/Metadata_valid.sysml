// XPECT noErrors ---> ""
package MetadataTest {
	public import 'User Defined Extensions'::*;
	
	library package 'User Defined Extensions' {
		
		enum def ClassificationLevel {
			uncl;
			conf;
			secret;
		}
		
		metadata def Classified {
			ref :>> annotatedElement : SysML::PartUsage;
			attribute classificationLevel : ClassificationLevel[1];
		}
		
		metadata def Security;
	}
	
	part x {
		metadata Classified {
			classificationLevel = ClassificationLevel::conf;
		}
		metadata Security;
	}
	
	part y {
		@Classified {
			classificationLevel = ClassificationLevel::conf;
		}
		@Security;
	}
	
	private #Classified #Security part z1;
	abstract #Security z2;
	
	#Security action a {
		#Security fork;
	}
	
}

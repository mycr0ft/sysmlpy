// XPECT noErrors ---> ""
package ElementFilterTest {
	abstract metadata def PartInfo {
		attribute isMandatory: ScalarValues::Boolean[0..1];
	}
	metadata def Safety :> PartInfo;
	metadata def Security :> PartInfo {
		attribute :> isMandatory = false;
	}
	
	part vehicle1_c1 {
		part interior {
			part alarm {@Security;}
			part seatBelt[2] {@Safety{isMandatory = true;}}
			part frontSeat[2];
			part driverAirBag {@Safety;}
		}
		part bodyAssy {
			part body;
			part bumper {@Safety;}
			part keylessEntry {@Security;}
		}
		part wheelAssy {
			part wheel[2];
			part antilockBrakes[2] {@Safety{isMandatory = false;}}
		}
	}
	
	package 'Safety Features' {
		public import vehicle1_c1::**;
		filter @Safety;
	}
	
	package 'Security Features' {
		public import vehicle1_c1::interior::*[@Security];
	}
	
	package 'Safety & Security Features' {
		public import vehicle1_c1::**;
		filter @Safety or @Security;
	}
	
	package 'Mandatory Features' {
		public import vehicle1_c1::**[@Safety and (as PartInfo).isMandatory];
	}
}

// XPECT noErrors ---> ""
package TradeStudyTest {
	public import TradeStudies::*;
	
	part def Engine;
	part engine1: Engine;
	part engine2: Engine;
	
	analysis engineTradeStudy : TradeStudy {
		subject : Engine[1..*] = (engine1, engine2);
		objective : MaximizeObjective;

		calc :>> evaluationFunction {
			in part : Engine;
			return : ScalarValues::Real;
		}
		
		return part : Engine;
	}
	
}
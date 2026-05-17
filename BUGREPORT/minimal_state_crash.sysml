/*
 * Minimal State Machine Test Case
 * 
 * This is the simplest possible state machine that crashes sysmlpy.
 * Removing ANY element makes it parse successfully.
 */

package MinimalStateMachineTest {
    
    state def SimpleSM {
        state stateA;
        state stateB;
        
        transition a_to_b
            first stateA
            then stateB;
    }
}

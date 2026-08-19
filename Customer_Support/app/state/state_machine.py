from transitions import Machine

class DisputeStateMachine:
    states = [
        'START',
        'INTENT_IDENTIFIED',
        'TRANSACTION_IDENTIFIED',
        'AMOUNT_CONFIRMED',
        'TRANSACTION_CONFIRMED',
        'CURRENT_CALL_AUTHORIZED',
        'DISPUTE_DETAILS_COLLECTED',
        'CUSTOMER_CONFIRMATION',
        'DISPUTE_CREATED',
        'COMPLETED'
    ]

    def __init__(self, current_state='START'):
        self.machine = Machine(model=self, states=DisputeStateMachine.states, initial=current_state)

        # Define transitions
        self.machine.add_transition(trigger='identify_intent', source='START', dest='INTENT_IDENTIFIED')
        self.machine.add_transition(trigger='identify_transaction', source='INTENT_IDENTIFIED', dest='TRANSACTION_IDENTIFIED')
        self.machine.add_transition(trigger='confirm_amount', source='TRANSACTION_IDENTIFIED', dest='AMOUNT_CONFIRMED')
        self.machine.add_transition(trigger='confirm_transaction', source='AMOUNT_CONFIRMED', dest='TRANSACTION_CONFIRMED')
        self.machine.add_transition(trigger='authorize_call', source='TRANSACTION_CONFIRMED', dest='CURRENT_CALL_AUTHORIZED')
        self.machine.add_transition(trigger='collect_details', source='CURRENT_CALL_AUTHORIZED', dest='DISPUTE_DETAILS_COLLECTED')
        self.machine.add_transition(trigger='confirm_customer', source='DISPUTE_DETAILS_COLLECTED', dest='CUSTOMER_CONFIRMATION')
        self.machine.add_transition(trigger='create_dispute', source='CUSTOMER_CONFIRMATION', dest='DISPUTE_CREATED')
        self.machine.add_transition(trigger='complete_task', source='DISPUTE_CREATED', dest='COMPLETED')

        # Rollback transitions (interruption)
        for i in range(1, len(self.states)):
            self.machine.add_transition(trigger='rollback', source=self.states[i], dest=self.states[i-1])

    def get_pending_steps(self):
        current_idx = self.states.index(self.state)
        return self.states[current_idx + 1:]

    def get_completed_steps(self):
        current_idx = self.states.index(self.state)
        return self.states[:current_idx]

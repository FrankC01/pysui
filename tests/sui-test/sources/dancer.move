/// Base module for sui
module pysuidance::dancer {
    use sui::transfer;
    use std::vector;
    use sui::object::{Self, UID};
    use sui::tx_context::{Self, TxContext};

    /// Does not contain value
    const DoesNotExist: u64 = 2;
    /// Wrong value removed
    const ValueDropMismatch: u64 = 3;

    /// Individual account trackers
    struct Tracker has key, store  {
        id: UID,
        initialized: bool,
        accumulator: vector<u8>,
    }

    /// Initialize new deployment
    fun init(ctx: &mut TxContext) {
        let admin = tx_context::sender(ctx);
        transfer::transfer(
            Tracker {
                id: object::new(ctx),
                initialized: true,
                accumulator: vector[],
            },
            admin
        );

    }

    /// Override for transfer of tracker
    public fun transfer(tracker: Tracker, recipient: address) {
        transfer::transfer<Tracker>(tracker, recipient)
    }

    /// Get the accumulator length
    fun stored_count(self: &Tracker) : u64 {
        vector::length<u8>(&self.accumulator)
    }

    /// Add an element to the accumulator
    fun add_to_store(self: &mut Tracker, value: u8) : u64 {
        vector::push_back<u8>(&mut self.accumulator, value);
        stored_count(self)
    }

    /// Add a series of vaues to the accumulator
    fun add_from(self: &mut Tracker, other:vector<u8>) {
        vector::append<u8>(&mut self.accumulator, other);
    }

    /// Check accumulator contains value
    fun has_value(self: &Tracker, value: u8) : bool {
        vector::contains<u8>(&self.accumulator, &value)
    }

    /// Removes a value from the accumulator
    fun drop_from_store(self: &mut Tracker, value: u8) : u8 {
        let (contained, idx) = vector::index_of<u8>(&self.accumulator, &value);
        assert!(contained, DoesNotExist);
        vector::remove<u8>(&mut self.accumulator, idx)
    }

    /// Add single value to accumulator
    public entry fun add_value(tracker: &mut Tracker, value: u8, _ctx: &mut TxContext) {
        // Verify ownership
        add_to_store(tracker,value);
    }

    /// Add single value to accumulator
    public entry fun remove_value(tracker: &mut Tracker, value: u8, _ctx: &mut TxContext) {
        // Verify ownership
        assert!(drop_from_store(tracker, value) == value,ValueDropMismatch);

    }
    /// Add multiple values to accumulator
    public entry fun add_values(tracker: &mut Tracker, values: vector<u8>, _ctx: &mut TxContext) {
        add_from(tracker, values);
    }


}

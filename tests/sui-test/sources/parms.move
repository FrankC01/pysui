/// Module: sui-parm
module suiparm::parms;

use std::string::{String,utf8};
use sui::coin::{Coin,from_balance};
use sui::sui::SUI;
use sui::balance;
use sui::vec_map;
use sui::event;
use sui::dynamic_field as df;

const EServiceFee:u64 = 1000000;
const Version:u8 = 1;

public struct ParmEvent has copy, drop {
    foo: u8
}

public struct AKind has copy, drop, store {
    a_u8: u8
}

public struct Phoney has key, store {
    id: UID,
    
}

public struct MayType<K: copy> has copy, drop, store {
    inner: K,
}

public enum ParmEnum has store {
    DIRECT(u8),
    RGB{red:u8, green: u8,blue:u8},
    MTO(u8,u8),
    MTS(ParmStruct)
}

public struct ParmScalars has store {
    f_u8: u8,
    f_u16: u16,
    f_u32: u32,
    f_u64: u64,
    f_u128: u128,
    f_u256: u256,
    f_o_u8: Option<u8>,
    f_address: address,
    f_vector: vector<u8>,
    f_nest_vector: vector<vector<ParmStruct>>,
    f_optional: Option<ParmStruct>,
    f_vec_map: vec_map::VecMap<u64,u64>,
    f_enum: ParmEnum
}

public struct ParmObject has key {
    id: UID,
    innards: ParmScalars,
    service: balance::Balance<SUI>,
    myname: String,
    mytype: MayType<AKind>
}

public fun create_parm_object(ctx: &mut TxContext): ParmObject {
    let mut po = ParmObject { id: object::new(ctx),
        service:balance::zero(),
        myname: utf8(b"foo"),
        mytype: MayType<AKind> { inner:AKind{a_u8:15} },
        innards:ParmScalars{
            f_u8:0,
            f_u16:0,
            f_u32:0,
            f_u64:0,
            f_u128:0,
            f_u256:0,
            f_o_u8:option::none<u8>(),
            f_address:ctx.sender(),
            f_vector:vector::empty<u8>(),
            f_nest_vector:vector::empty<vector<ParmStruct>>(),
            f_optional:option::none<ParmStruct>(),
            f_vec_map:vec_map::empty<u64,u64>(),
            f_enum:ParmEnum::DIRECT(0)}};
    set_object_version(&mut po);
    po
}

/// Checks for version and sets if not existent yet
fun set_object_version(po:&mut ParmObject) {

    if (df::exists_(&po.id, b"version")) {
    } else {
        df::add(
            &mut po.id,
            b"version",
            Version
        );    
    }
}

#[allow(unused_field)]
public struct ParmStruct has store{
    index:u8
}


/// Check uncommon uint type
public fun check_uints(_a: u16, _b: u32, _c: u64, _d: u128, _e: u256, _ctx: &mut TxContext) {
    event::emit(ParmEvent { foo: 0 })
}


/// Check uncommon uint type
public fun check_optional_uints(
    _a: Option<u16>,
    _b: Option<u32>,
    _c: Option<u64>,
    _d: Option<u128>,
    _e: Option<u256>,
    _ctx: &mut TxContext,
) {event::emit(ParmEvent { foo: 1 })}

/// Check vectors of uints
public fun check_uints_vectors(
    _a: vector<u16>,
    _b: vector<u32>,
    _c: vector<u64>,
    _d: vector<u128>,
    _e: vector<u256>,
    _ctx: &mut TxContext,
) {}

/// Check vectors of option uints
public fun check_optional_uint_vectors(
    _a: Option<vector<u16>>,
    _b: Option<vector<u32>>,
    _c: Option<vector<u64>>,
    _d: Option<vector<u128>>,
    _e: Option<vector<u256>>,
    _ctx: &mut TxContext,
) {}

/// Check vector of u8 only for bytes or str conversions
public fun check_vec_u8(_c: vector<u8>, _ctx: &mut TxContext) {}

/// Check optional vec of u8 only
public fun check_vec_optional_u8(_c: Option<vector<u8>>, _ctx: &mut TxContext) {}

/// Check vector nesting of u8
public fun check_vec_deep_u8(_c: vector<vector<vector<u8>>>, _ctx: &mut TxContext) {}

/// Check vector of addresses
public fun check_address_vec(_a: vector<address>, _ctx: &mut TxContext) {}

/// Check vector of identifiers
public fun check_id_vec(_a: vector<ID>, _ctx: &mut TxContext) {}

/// Check String
public fun check_string(_a: &String, _ctx: &mut TxContext) {}

/// Check Optional String
public fun check_string_option(_a: Option<String>, _ctx: &mut TxContext) {}

/// Check vector of String
public fun check_string_vec(_a: vector<String>, _ctx: &mut TxContext) {}

/// Check vector of optional String
public fun check_vec_option_string(_a: vector<Option<String>>, _ctx: &mut TxContext) {}

public fun swap_a_b<T>(_arg1: vector<Coin<T>>, _arg10: &mut TxContext): vector<Coin<T>> {
    _arg1
}

public fun check_bool(_arg1: bool, _ctx: &mut TxContext) {}

public fun get_sender(ctx: &mut TxContext): address {
    ctx.sender()
}

public fun check_all<T:copy + drop>(
    _arg1:bool,
    _arg2:u8,
    _arg3:u256,
    _arg4:String,
    _arg5:Option<String>,
    _arg6:vector<u8>,
    _arg7:vector<String>,
    _arg8:&ParmScalars,
    _arg9:vector<MayType<T>>, 
    _arg10: &mut TxContext) {}

fun init(ctx:&mut TxContext) {
    let pobj = create_parm_object(ctx);
    // let pobj = ParmObject {id:object::new(ctx),service:balance::zero()};
    transfer::transfer(pobj, ctx.sender())
}

#[allow(lint(self_transfer))]
public fun create_phoney(ctx:&mut TxContext){
    let phny = Phoney{id: object::new(ctx)};
    transfer::transfer(phny, ctx.sender());
}

public fun check_phoney(phny:&mut Option<Phoney>,_ctx:&mut TxContext) :bool {
    if (phny.is_some()) {        
        true
    } else {
        false
    }
}

public fun burn_phoney(phny:Phoney,_ctx:&mut TxContext) {
    let Phoney {id} = phny;
    id.delete();
}

public fun pay_service(self:&mut ParmObject,payfrom:&mut Coin<SUI>,_ctx:&mut TxContext) {
    set_object_version(self);
    let pbal = payfrom.balance_mut();
    self.service.join(pbal.split(EServiceFee));
}

public fun get_service(self:&mut ParmObject, amount:&mut Option<u64>,ctx:&mut TxContext) : Coin<SUI> {
    set_object_version(self);
    // If an amount is specified, split from current service balance
    let pbal = if (amount.is_some()) {
        let amval:u64 = amount.extract();
        self.service.split(amval)
    // Otherwise take it all
    } else {
        self.service.withdraw_all()
    };
    // Create and return a new Sui coin from balance
    from_balance<SUI>(pbal,ctx)
}

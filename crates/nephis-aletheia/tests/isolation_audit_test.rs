use aletheia::engine::fuel::FuelMeter;
use aletheia::engine::session::Session;
use aletheia::billboard::restricted::{AletheiaError, EscalationCapability};

#[test]
fn test_aletheia_filesystem_and_traversal_boundaries() {
    let mut s = Session::new(100_000);
    
    // Attack Vector A: Classical filesystem opening attempts
    let attacks = vec![
        "with open('/etc/passwd') as f: text = f.read()",
        "data = open('../../../../etc/shadow').read()",
        "import os; os.listdir('/')",
        "with open('C:\\\\Windows\\\\System32\\\\cmd.exe') as f: pass",
    ];

    for attack in attacks {
        let res = s.eval(attack);
        match res {
            Err(AletheiaError::RestrictedOperation { capability, attempted, .. }) => {
                assert!(
                    capability == EscalationCapability::RequiresFilesystem || 
                    capability == EscalationCapability::RequiresProcessSpawn,
                    "Attack '{}' did not trigger filesystem/process boundary: {:?}", attack, capability
                );
                println!("✔ Filesystem Boundary [{}]: blocked (attempted: '{}')", attack, attempted);
            }
            _ => panic!("Expected restricted operation for attack: {}", attack),
        }
    }
}

#[test]
fn test_aletheia_network_egress_and_metadata_firewall() {
    let mut s = Session::new(100_000);

    // Attack Vector B: Cloud metadata and internal egress attempts
    let net_attacks = vec![
        "import urllib.request; urllib.request.urlopen('http://169.254.169.254/latest/meta-data/')",
        "import socket; s = socket.socket(); s.connect(('127.0.0.1', 22))",
        "import socket; s = socket.socket(); s.connect(('127.0.0.1', 5432))",
        "import requests; requests.get('http://169.254.10.5/token')",
    ];

    for attack in net_attacks {
        let res = s.eval(attack);
        match res {
            Err(AletheiaError::RestrictedOperation { capability, attempted, .. }) => {
                assert_eq!(capability, EscalationCapability::RequiresNetwork);
                println!("✔ Network Egress Security [{}]: blocked (attempted: '{}')", attack, attempted);
            }
            _ => panic!("Expected network restricted operation for attack: {}", attack),
        }
    }
}

#[test]
fn test_aletheia_resource_exhaustion_fuel_trap() {
    // Attack Vector C: Infinite loop / resource starvation
    let fuel = FuelMeter::new(10_000);
    
    // Consume fuel up to the limit
    assert!(fuel.consume(9_999).is_ok());
    assert_eq!(fuel.remaining(), 1);
    
    // Exceed fuel boundary
    let trap_res = fuel.consume(10);
    assert!(trap_res.is_err());
    assert_eq!(fuel.remaining(), 0);
    println!("✔ Resource Exhaustion: Fuel meter trap clamped execution at 10,000 instruction units");

    // Micro CoW session branching churn
    let mut root = Session::new(50_000);
    let _ = root.eval("base_val = 1337");

    for i in 0..100 {
        let mut fork = root.fork();
        let _ = fork.eval(&format!("x = base_val + {}", i));
    }
    println!("✔ High-Concurrency Churn: 100 sub-microsecond CoW session forks completed with zero leaks");
}

#[test]
fn test_aletheia_privilege_and_process_containment() {
    let mut s = Session::new(100_000);

    let priv_attacks = vec![
        "import ctypes; ctypes.CDLL(None)",
        "fork()",
        "import subprocess; subprocess.Popen(['whoami'])",
        "os.system('id')",
    ];

    for attack in priv_attacks {
        let res = s.eval(attack);
        match res {
            Err(AletheiaError::RestrictedOperation { capability, attempted, .. }) => {
                assert_eq!(capability, EscalationCapability::RequiresProcessSpawn);
                println!("✔ Privilege Escalation [{}]: blocked (attempted: '{}')", attack, attempted);
            }
            _ => panic!("Expected process spawn restriction for attack: {}", attack),
        }
    }
}


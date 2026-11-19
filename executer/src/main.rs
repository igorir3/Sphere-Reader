use std::process::Command;
use std::env;

#[cfg(target_os = "windows")]
fn main() -> std::io::Result<()> {
    let mut args: Vec<String> = env::args().collect();

    let exe_path = env::current_exe()?;
    let exe_dir = exe_path.parent().unwrap();
    
    let args_len = args.len();
    args.retain(|x| x != "--notw");
    let programm = if args_len == args.len() {"python\\pythonw.exe"} else {"python\\python.exe"};

    env::set_current_dir(exe_dir)?;

    if args.len() > 0 {
        if args[0].ends_with(".exe"){
            args[0] = "main.py".to_string();
        } else {
            args.insert(0, "main.py".to_string());
        }
    } else {
        args.insert(0, "main.py".to_string());
    }

    println!("{programm} {args:?}");
    
    Command::new(programm)
            .args(args)
            .spawn()
            .expect("program should be started");

    Ok(())
}

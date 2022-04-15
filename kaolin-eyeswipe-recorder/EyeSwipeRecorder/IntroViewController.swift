//
//  IntroViewController.swift
//  EyeSwipeRecorder
//
//

import UIKit

class IntroViewController: UIViewController {
    
    @IBOutlet weak var textField: UITextField!
    var userEmail : String?
    override func viewDidLoad() {
        super.viewDidLoad()
        
    } 
    @IBAction func emailEnter(_ sender: UITextField) {
        userEmail = sender.text!
    }
    @IBAction func buttonPressed(_ sender: Any) {
        if textField.isFirstResponder {
            userEmail = textField.text!
            textField.resignFirstResponder()
        }
    }
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if let vc = segue.destination as? ViewController {
            vc.userEmail = userEmail
        }
    }
    override func shouldPerformSegue(withIdentifier identifier: String, sender: Any?) -> Bool {
        return userEmail != nil
    }
    

    /*
    // MARK: - Navigation

    // In a storyboard-based application, you will often want to do a little preparation before navigation
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        // Get the new view controller using segue.destination.
        // Pass the selected object to the new view controller.
    }
    */

}

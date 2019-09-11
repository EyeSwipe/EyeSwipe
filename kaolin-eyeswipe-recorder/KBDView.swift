//
//  KBDView.swift
//  EyeSwipeRecorder
//

// see also all this cool shit: https://developer.apple.com/documentation/uikit/uikeyinput
// maybe differently interesting: https://developer.apple.com/library/archive/documentation/StringsTextFonts/Conceptual/TextAndWebiPhoneOS/KeyboardManagement/KeyboardManagement.html
/*
// https://stackoverflow.com/questions/13005969/it-is-possible-to-show-keyboard-without-using-uitextfield-and-uitextview-iphone
For anyone, who wants to show keyboard without UITextField/UITextView for some reasons, could easily extend some view, which requires text input by implementing UIKeyInput protocol and canBecomeFirstResponder method.
And if you override @property (nullable, readwrite, strong) UIView *inputAccessoryView; in the new class you can assign an inputAccessoryView to it too. – Alexandre G Mar 15 '16 at 4:52
Your control that implements UIKeyInput can also implement UITextInputTraits if you want to customize the keyboard :) – Nathan Kot Apr 8 '16 at 2:13
*/

import Foundation
import UIKit

class KBDView: UIView, UIKeyInput, UITextInputTraits {
	var hasText: Bool = false
	
	func insertText(_ text: String) {
		if text == " " {
			NotificationCenter.default.post(name: .eyeswipeOnSpacebar, object: nil)
		}
	}
	
	func deleteBackward() {
		// pass :)
		NotificationCenter.default.post(name: .eyeswipeCancel, object: nil)
	}
	
	override var canBecomeFirstResponder: Bool {
		return true
	}
	
	var autocorrectionType: UITextAutocorrectionType {
		get {
			return .no
		}
		set {
		}
	}

	// class definition goes here
}

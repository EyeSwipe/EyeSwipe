//
//  CameraController.swift
//  EyeSwipeRecorder
//

// BETTER HANDLING OF THINGS, BUT IOS 13 (internet seems to have been scrubbed of iOS 12 version) —
// https://developer.apple.com/documentation/avfoundation/cameras_and_media_capture/avcam_building_a_camera_app
// still has good info

import AVFoundation
import UIKit
import Photos

class CameraController: NSObject, AVCaptureFileOutputRecordingDelegate {
	var captureSession: AVCaptureSession?
	
	var frontCamera: AVCaptureDevice?
	var frontCameraInput: AVCaptureDeviceInput?
	var cancelling:Bool = false
	
	var previewLayer: AVCaptureVideoPreviewLayer?
	
	private var movieFileOutput: AVCaptureMovieFileOutput?
	private var backgroundRecordingID: UIBackgroundTaskIdentifier?
	private let sessionQueue = DispatchQueue(label: "session queue") // Communicate with the session and other session objects on this queue.
	
	func displayPreview(on view: UIView) throws {
		guard let captureSession = self.captureSession, captureSession.isRunning else { throw CameraControllerError.captureSessionIsMissing }
		
		self.previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
		self.previewLayer?.videoGravity = AVLayerVideoGravity.resizeAspectFill
		self.previewLayer?.connection?.videoOrientation = .portrait
		
		view.layer.insertSublayer(self.previewLayer!, at: 0)
		self.previewLayer?.frame = view.frame
	}
	
	// from AVCam example, bits and hacks
	
	func completeRecording() {
		movieFileOutput?.stopRecording()
	}
	
	func cancelRecording() {
		cancelling = true
		movieFileOutput?.stopRecording()
		// TODO: cancel needs more logic strung throughout, remember it's canceling, oh if we cared about threading and race conditions oh my ;)
	}
	
	func startRecording(word:String) {
		guard let movieFileOutput = self.movieFileOutput else {
			return
		}
		sessionQueue.async {
			if !movieFileOutput.isRecording {
				if UIDevice.current.isMultitaskingSupported {
					/*
					Setup background task.
					This is needed because the `capture(_:, didFinishRecordingToOutputFileAt:, fromConnections:, error:)`
					callback is not received until AVCam returns to the foreground unless you request background execution time.
					This also ensures that there will be time to write the file to the photo library when AVCam is backgrounded.
					To conclude this background execution, endBackgroundTask(_:) is called in
					`capture(_:, didFinishRecordingToOutputFileAt:, fromConnections:, error:)` after the recorded file has been saved.
					*/
					self.backgroundRecordingID = UIApplication.shared.beginBackgroundTask(expirationHandler: nil)
				}
				
				// Update the orientation on the movie file output video connection before starting recording.
				let movieFileOutputConnection = movieFileOutput.connection(with: .video)
				//					movieFileOutputConnection?.videoOrientation = previewLayer?.orie
				print("TODO: movie orientation???")
				
				let availableVideoCodecTypes = movieFileOutput.availableVideoCodecTypes
				
				if availableVideoCodecTypes.contains(.hevc) {
					movieFileOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.hevc], for: movieFileOutputConnection!)
				}
				
				// Start recording to a temporary file.
				let outputFileName = word + "_" + NSUUID().uuidString
				let outputFilePath = (NSTemporaryDirectory() as NSString).appendingPathComponent((outputFileName as NSString).appendingPathExtension("mov")!)
				movieFileOutput.startRecording(to: URL(fileURLWithPath: outputFilePath), recordingDelegate: self)
			} else {
				movieFileOutput.stopRecording()
			}
		}
	}
	
	func fileOutput(_ output: AVCaptureFileOutput, didStartRecordingTo fileURL: URL, from connections: [AVCaptureConnection]) {
		// Enable the Record button to let the user stop the recording.
		DispatchQueue.main.async {
			//self.recordButton.isEnabled = true
			//self.recordButton.setTitle(NSLocalizedString("Stop", comment: "Recording button stop title"), for: [])
			print("OK THEN RECORDING STARTED")
		}
	}
	
	func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
		/*
		Note that currentBackgroundRecordingID is used to end the background task
		associated with this recording. This allows a new recording to be started,
		associated with a new UIBackgroundTaskIdentifier, once the movie file output's
		`isRecording` property is back to false — which happens sometime after this method
		returns.
		
		Note: Since we use a unique file path for each recording, a new recording will
		not overwrite a recording currently being saved.
		*/
		func cleanUp() {
			let path = outputFileURL.path
			if FileManager.default.fileExists(atPath: path) {
				do {
					try FileManager.default.removeItem(atPath: path)
				} catch {
					print("Could not remove file at url: \(outputFileURL)")
				}
			}
			
			if let currentBackgroundRecordingID = self.backgroundRecordingID {
				backgroundRecordingID = UIBackgroundTaskInvalid
				if currentBackgroundRecordingID != UIBackgroundTaskInvalid {
					UIApplication.shared.endBackgroundTask(currentBackgroundRecordingID)
				}
			}

			NotificationCenter.default.post(name: .eyeswipeVideoComplete, object: nil)

		}
		
		var success = true
		
		if error != nil {
			print("Movie file finishing error: \(String(describing: error))")
			success = (((error! as NSError).userInfo[AVErrorRecordingSuccessfullyFinishedKey] as AnyObject).boolValue)!
		}
		
		if (cancelling) {
			cancelling = false
			cleanUp()
		} else if success {
			// Check authorization status.
			PHPhotoLibrary.requestAuthorization { status in
				if status == .authorized {
					// Save the movie file to the photo library and cleanup.
					PHPhotoLibrary.shared().performChanges({
						let options = PHAssetResourceCreationOptions()
						options.shouldMoveFile = true
						let creationRequest = PHAssetCreationRequest.forAsset()
						creationRequest.addResource(with: .video, fileURL: outputFileURL, options: options)
					}, completionHandler: { success, error in
						if !success {
							print("Could not save movie to photo library: \(String(describing: error))")
						}
						cleanUp()
					}
					)
				} else {
					cleanUp()
				}
			}
		} else {
			cleanUp()
		}
		
		// Enable the Camera and Record buttons to let the user switch camera and start another recording.
		DispatchQueue.main.async {
			// Only enable the ability to change camera if the device has more than one camera.
			print("ALLDONE")
		}
	}
	
}

extension Notification.Name {
	static let eyeswipeOnSpacebar = Notification.Name("eyeswipe-on-spacebar")
	static let eyeswipeCancel = Notification.Name("eyeswipe-cancel")
	static let eyeswipeVideoComplete = Notification.Name("eyeswipe-videocomplete")
}

extension CameraController {
	func prepare(completionHandler: @escaping (Error?) -> Void) {
		func createCaptureSession() {
			self.captureSession = AVCaptureSession()
		}
		
		func configureCaptureDevices() throws {
			
			let session = AVCaptureDevice.DiscoverySession(deviceTypes: [.builtInWideAngleCamera], mediaType: AVMediaType.video, position: .unspecified)
			
			let cameras = session.devices.compactMap { $0 }
			guard !cameras.isEmpty else { throw CameraControllerError.noCamerasAvailable }
			
			for camera in cameras {
				if camera.position == .front {
					self.frontCamera = camera
				}
			}
		}
		
		func configureDeviceInputs() throws {
			guard let captureSession = self.captureSession else { throw CameraControllerError.captureSessionIsMissing }
			
			if let frontCamera = self.frontCamera {
				self.frontCameraInput = try AVCaptureDeviceInput(device: frontCamera)
				
				if captureSession.canAddInput(self.frontCameraInput!) { captureSession.addInput(self.frontCameraInput!) }
				else { throw CameraControllerError.inputsAreInvalid }
				
			}
				
			else { throw CameraControllerError.noCamerasAvailable }
		}
		
		func configureOutput() throws {
			guard let captureSession = self.captureSession else { throw CameraControllerError.captureSessionIsMissing }
			let movieFileOutput = AVCaptureMovieFileOutput()
			
			if captureSession.canAddOutput(movieFileOutput) {
				captureSession.beginConfiguration()
				captureSession.addOutput(movieFileOutput)
				captureSession.sessionPreset = .high
				if let connection = movieFileOutput.connection(with: .video) {
					if connection.isVideoStabilizationSupported {
						connection.preferredVideoStabilizationMode = .auto
					}
				}
				captureSession.commitConfiguration()
				self.movieFileOutput = movieFileOutput
				captureSession.startRunning()
			}
		}
			
			DispatchQueue(label: "prepare").async {
				do {
					createCaptureSession()
					try configureCaptureDevices()
					try configureDeviceInputs()
					try configureOutput()
				}
					
				catch {
					DispatchQueue.main.async {
						completionHandler(error)
					}
					
					return
				}
				
				DispatchQueue.main.async {
					completionHandler(nil)
				}
			}
		}
}

extension CameraController {
	enum CameraControllerError: Swift.Error {
		case captureSessionAlreadyRunning
		case captureSessionIsMissing
		case inputsAreInvalid
		case invalidOperation
		case noCamerasAvailable
		case unknown
	}
	
	public enum CameraPosition {
		case front
		case rear
	}
}

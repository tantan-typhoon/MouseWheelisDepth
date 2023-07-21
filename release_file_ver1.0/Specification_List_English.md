## Proposed Specification Schedule
*Planned for implementation in ver1.0*

- [ ] posemode
	
	- [ ] Spec: Posebone's head-tail vector direction and scale will follow the mouse.

	- [ ] Spec: Addition of shortcut keys, shift+R, shift+T, shift+F.

	- [ ] Spec: Ability to set the sensitivity (wheel grid distance) when the wheel is moved.

	- [ ] Spec: Option to either change the length or just the direction during posebone operation.

	- [ ] Spec: Option panel
		- Creation of a custom property toggle (boolm function).
		- Inclusion of the custom property toggle in the panel class.
		- Decisions based on the state of the custom property toggle.
		- Option to use the guide ball.

- [ ] objectmode
	- [ ] Spec: Movement of the object's location based on the mouse's region position and the wheel rotation count.
	
	- [ ] Spec: Rotation of the object's base axis vector direction based on the mouse's region position and the wheel rotation count.

	- [ ] Spec: Option panel
		- Option to change the object's base axis vector (When a vector is input, that unit vector becomes the base axis vector. By default, the Z-axis of the local coordinates is set as the base axis vector).
		- Select button to decide whether or not to use the guide ball object.

- [ ] General
	
	- [ ] Deciding on items to be added to preferences
		- Assignment of shortcut keys.

	- [ ] Enabling modal mode exit through the esc key and left click.

	- [ ] Specification of license.




*Planned for implementation in ver1.1 and later*

- [ ] 
	
	- [ ] Spec: Option to draw a point at the target point.

	- [ ] Spec: Enabling of rotation and movement operations even during mesh editing.

	- [ ] Spec: Development of a wipe-like feature that allows viewing from a different angle how far you have proceeded into the depth.

	- [ ] Spec: Creation of a circle that changes in size according to the degree of depth progression via the mouse wheel.

	- [ ] Spec: Option to change the shape or color of the guide object in accordance with the degree of depth progression via the mouse wheel.

	- [ ] Spec: Display the depth progression degree in meters with the mouse wheel in text.

	- [ ] Spec: In case of multiple objects selected, apply rotation to all.

	- [ ] Spec: Change the wheel grid distance to 1/2 or 2 times using the mouse side button, or make it changeable at a set rate in options.

	- [ ] Spec: Enable simultaneous operations even when multiple selections are made.

	- [ ] Spec: Enable rotation around the posebone's head-tail axis (Switch to head-tail axis rotation mode with right click, operate the quaternion around the axis).

	- [ ] Spec: Ability to display rotation gizmo (displayable with bpy.context.space_data.show_gizmo_object_rotate = True).

	- [ ] Spec: Sensitivity adjustment option, when the posebone angle moves a lot, automatically reduce the sensitivity of the wheel grid distance to finely subdivide (associate the difference in the angle and distance that moves in one wheel, stabilize it, make it constant). Side button is Type A, sensitivity auto option is Type B.

	- [ ] Spec: Display an operation guide in text (end with left click, transition to axis rotation with right click, Type A or Type B (sensitivity auto mode or side button adjustment mode), etc.).

	- [ ] Spec: Adjust distance according to the magnification displayed by the camera (automatically adjust sensitivity based on the proportion of object size occupying the region screen).

	- [ ] Spec: Create a mode where the wheel goes back and completes a full rotation.

	- [ ] Spec: The initial angle at the start of operator should be the original bone position.

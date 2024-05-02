// Start kaboom
kaboom()

// Load assets
loadSprite("char", "./sprites/character02r.png", {
	// The image contains 9 frames layed out horizontally, slice it into individual frames
	sliceX: 4,
    sliceY: 4,
	// Define animations
	anims: {
		"idle": {
            from: 6,
            to: 9,
            loop: true,
            speed: 3,
        },
        "run": {
            from: 2,
            to: 5,
            loop: true,
            speed: 10,
        },
		// This animation only has 1 frame
		"jump": 1,
	},
})

loadSprite("grass", "./sprites/grassr.png")

loadSound("jumpland", "./sounds/jumpland.wav")

// Set the gravity acceleration (pixels per second)
setGravity(1600)

const SPEED = 600

// Add player game object
const player = add([
	sprite("char"),
	pos(center()),
	area(),
	// body() component gives the ability to respond to gravity
	body(),
])

player.play("idle")

onKeyPress("space", () => {
	if (player.isGrounded()) {
		player.jump()
		player.play("jump")
	}
})
onKeyPress("up", () => {
	if (player.isGrounded()) {
		player.jump()
		player.play("jump")
	}
})

player.onGround(() => {
    play("jumpland")
	if (!isKeyDown("left") && !isKeyDown("right")) {
		player.play("idle")
	} else {
		player.play("run")
	}
})

onKeyDown("left", () => {
	player.move(-SPEED, 0)
	player.flipX = true
    if (player.isGrounded() && player.curAnim() !== "run") {
		player.play("run")
	}
})

onKeyDown("right", () => {
	player.move(SPEED, 0)
	player.flipX = false
    if (player.isGrounded() && player.curAnim() !== "run") {
		player.play("run")
	}
})

;["left", "right"].forEach((key) => {
	onKeyRelease(key, () => {
	// Only reset to "idle" if player is not holding any of these keys
		if (player.isGrounded() && !isKeyDown("left") && !isKeyDown("right")) {
			player.play("idle")
		}
	})
})

// Add a platform to hold the player
add([
	rect(width(), 48),
	outline(4),
	area(),
	pos(0, height() - 48),
	// Give objects a body() component if you don't want other solid objects pass through
	body({ isStatic: true }),
])
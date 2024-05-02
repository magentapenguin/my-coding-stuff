// Start kaboom
kaboom({
	background: [141, 183, 255],
})

// Load assets
loadSprite("char", "./sprites/character03r.png", {
	// The image contains 9 frames layed out horizontally, slice it into individual frames
	sliceX: 10,
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
            speed: 15,
        },
		// This animation only has 1 frame
		"jump": 1,
	},
})

loadSprite("portal", "./sprites/portalr.png", {
	sliceX: 4,
	// Define animations
	anims: {
		"spin": {
            from: 0,
            to: 3,
            loop: true,
            speed: 5,
        }
	},
})


loadSprite("grass", "./sprites/grassr.png")
loadSprite("spike", "./sprites/spiker.png")

loadSound("jumpland", "./sounds/jumpland.wav")
loadSound("happy", "./sounds/happy.mp3")

function handleout() {
	return {
		id: "handleout",
		require: [ "pos" ],
		update() {
			const spos = this.screenPos()
			if (
				spos.x < 0 ||
				spos.x > width() ||
				spos.y < 0 ||
				spos.y > height()
			) {
				// triggers a custom event when out
				this.trigger("out")
			}
		},
	}
}

// Set the gravity acceleration (pixels per second)
setGravity(1800)

const SPEED = 500

const level = addLevel([
	// Design the level layout with symbols
	"     ==       ^   ", 
	"          ======  ",
	"                  ",
	" @   ^^^^^        ",
	"==========   .    ",
	"             =====",
], {
	// The size of each grid
	tileWidth: 64,
	tileHeight: 64,
	// The position of the top left block
	pos: vec2(0, 0),
	// Define what each symbol means (in components)
	tiles: {
		"@": () => [
			sprite("char"),
			area({ scale: vec2(1, 0.9) }),
			body({jumpForce: SPEED*2}),
			anchor("bot"),
			"player",
		],
		"=": () => [
			sprite("grass"),
			area(),
			body({ isStatic: true }),
			anchor("bot"),
		],
		"^": () => [
			sprite("spike"),
			area({ scale: 0.2}),
			body({ isStatic: true }),
			anchor("bot"),
			"danger",
		],
        ".": () => [
            sprite("portal"),
            area(),
            body({ isStatic: true }),
            anchor("bot"),
            "portal",
        ],
	},
})
// Get the player object from tag
const player = level.get("player")[0]

const music = play("happy", {
	loop: true,
	paused: false,
})

level.get("portal")[0].play("spin")

player.play("idle")
debug.inspect = true
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

player.onCollide("danger", (x) => {
	player.pos = level.tile2Pos(0, 1)
})
player.onUpdate(() => {
	// center camera to player
	camPos(player.pos)
	// check fall death
	if (player.pos.y >= height()*2) {
		player.pos = level.tile2Pos(0, 1)
	}
    if (!player.isGrounded()) {
        player.play("jump")
    }
})
player.onPhysicsResolve(() => {
	// Set the viewport center to player.pos
	camPos(player.pos)
})
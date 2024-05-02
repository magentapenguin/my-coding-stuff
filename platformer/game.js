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

loadSprite("coin", "./sprites/coinr.png", {
	sliceX: 4,
	// Define animations
	anims: {
		"move": {
            from: 0,
            to: 3,
            loop: true,
            speed: 3,
        }
	},
})


loadSprite("grass", "./sprites/grassr.png")
loadSprite("spike", "./sprites/spiker.png")
loadSprite("steel", "./sprites/steelr.png")

loadSound("jumpland", "./sounds/jumpland.wav")
loadSound("happy", "./sounds/happy.mp3")
loadSound("empty", "./sounds/empty.wav")

loadFont("VT323", "./VT323-Regular.ttf")

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

const LEVELS = [
    [
        "     $$           ",
        "     ==       ^   ", 
        "          ======  ",
        "                  ",
        " @   ^^^^^        ",
        "==========   .    ",
        "             =====",
    ],
    [
        "    $$           ",
        "    ==                 ",
        "",
        "      $            |   ",
        "           |       |  ",
        "      |    |       |   ",
        "      |    |       |  ",
        "      |    |       |  ",
        "@     |^^^^|^^^^^^^|  .",
        "========================",
    ],
]

const LEVELCFG = {
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
            area({ scale: 0.2}),
            body({ isStatic: true }),
            anchor("bot"),
            "portal",
        ],
        "$": () => [
            sprite("coin"),
            area({ scale: 0.2}),
            body({ isStatic: true }),
            anchor("bot"),
            "coin",
        ],
        "|": () => [
            sprite("steel"),
            area(),
            body({ isStatic: true }),
            anchor("bot"),
        ],
	},
}

const music = play("happy", {
    loop: true,
    paused: false,
    volume: 0.5,
})

scene("game", ({ levelIdx, score }) => {

	// Use the level passed, or first level
	const level = addLevel(LEVELS[levelIdx || 0], LEVELCFG)

	
    // Get the player object from tag
    const player = level.get("player")[0]


    level.get("portal")[0].play("spin")
    level.get("coin").forEach((x)=>x.play("move"))

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

    player.onCollide("danger", (x) => {
        player.pos = level.tile2Pos(0, 1)
    })
    
    player.onCollide("coin", (coin) => {
		destroy(coin)
		score++
		scoreLabel.text = score
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
    player.onCollide("portal", () => {
		if (levelIdx < LEVELS.length - 1) {
			// If there's a next level, go() to the same scene but load the next level
			go("game", {
				levelIdx: levelIdx + 1,
				score: score,
			})
		} else {
			// Otherwise we have reached the end of game, go to "win" scene!
			go("win", { score: score })
		}
	})
    
    const scoreLabel = add([
		text(score, {font: "VT323"}),
		pos(12),
        fixed(),
	])
    
    onKeyPress(()=>play('empty'))
})

onKeyPress("r", () => {
    go("game", {
        levelIdx: 0,
        score: 0,
    })
})

function start() {
	// Start with the "game" scene, with initial parameters
	go("game", {
		levelIdx: 0,
		score: 0,
	})
}
start()
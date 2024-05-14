import kaboom from "https://cdn.jsdelivr.net/npm/kaboom/+esm";
import { addButton, onsize, patrol, cursormod, } from "./utills.js";

// Start kaboom
kaboom({
    canvas: document.getElementById('main'),
    background: [141, 183, 255]
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

loadSprite("fullscreen", "./sprites/fullscreen.png", {
    sliceX: 2,
    // Define animations
    anims: {
        "small": 1,
        "big": 0,
    },
})

loadSprite("coin", "./sprites/coinr.png", {
    sliceX: 8,
    // Define animations
    anims: {
        "move": {
            from: 0,
            to: 7,
            loop: true,
            speed: 5,
        }
    },
})


loadSprite("grass", "./sprites/grassr.png")
loadSprite("ghosty", "./sprites/ghostr.png")
loadSprite("spike", "./sprites/spiker.png")
loadSprite("wspike", "./sprites/widespiker.png")
loadSprite("steel", "./sprites/steelr.png")

loadSound("jumpland", "./sounds/jumpland.wav")
loadSound("happy", "./sounds/happy.mp3")
loadSound("empty", "./sounds/empty.wav")
loadSound("coin", "./sounds/coin1.wav")

loadFont("pixel", "'./Kitchen Sink.ttf'")

const credits = {
    'Kaboom.js - Game Framework':'https://kaboomjs.com', 
    'Polyducks - Font': 'https://polyducks.itch.io/kitchen-sink-font', 
    'MentalSanityOff - Fall Sound': 'http://www.freesound.org/people/MentalSanityOff/sounds/148796/', 
    'rezoner - Music': 'https://opengameart.org/content/happy-arcade-tune',
    'Luke.RUSTLTD - Coin Sound': 'https://opengameart.org/content/10-8bit-coin-sounds',
}

// Set the gravity acceleration (pixels per second)
setGravity(1800)

const SPEED = 500

const LEVELS = [
    [
        "             $$           ",
        "             ==       ^   ",
        "                   ======  ",
        "                            ",
        " @             ^^^^^        ",
        "====================   .    ",
        "                       =====",
    ],
    [
        "    $$           ",
        "    ==                 ",
        "                       ",
        "                   #   ",
        "      $    #       #  ",
        "      #    #       #   ",
        "      #    #       #  ",
        "      #    #       #  ",
        " @    #^^^^#^^^^^^^#  .",
        "========================",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "              . $$$$$",
        "              ========="
    ],
    [
        "          ",
        " . ^      ",
        "####      ",
        "          ",
        "        ##",
        "          ",
        "          ",
        "$^        ",
        "###      $",
        "         #",
        "          ",
        "    $$    ",
        "    ##    ",
        "          ",
        " @       ",
        "==="
    ],
    [
        "          *     $",
        "          #     $",
        "          #     $",
        "          #     $",
        "          #     $",
        "          #     $",
        "          #      ",
        " @  #   > #     .",
        "==================="
    ],
    [
        "                      * ",
        "                      # ",
        "           $          # ",
        "           $    *     # .",
        "      $         #$    ====",
        "      $         #      ",
        "                #      ",
        "                #      ",
        "@#^^^^>^^^^>^^^^#>^^^^^",
        "========================",
    ]
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
            pos(),
            area({ scale: vec2(1, 0.9) }),
            body({ jumpForce: SPEED * 2 }),
            anchor("bot"),
            "player",
        ],
        "=": () => [
            sprite("grass"),
            area(),
            body({ isStatic: true }),
            // odd that the offscreen component causes the game to lag
            //offscreen({ hide: true }),
            anchor("bot"),
        ],
        "^": () => [
            sprite("spike"),
            area({ scale: 0.2 }),
            body({ isStatic: true }),
            //offscreen({ hide: true }),
            anchor("bot"),
            "danger",
        ],
        "*": () => [
            sprite("wspike"),
            area({ scale: vec2(0.8, 0.2) }),
            body({ isStatic: true }),
            //offscreen({ hide: true }),
            anchor("bot"),
            "danger",
        ],
        ".": () => [
            sprite("portal"),
            area({ scale: vec2(0.5, 0.9) }),
            body({ isStatic: true }),
            //offscreen({ hide: true }),
            anchor("bot"),
            "portal",
        ],
        "$": () => [
            sprite("coin"),
            area({ scale: vec2(0.5,0.8) }),
            //offscreen({ hide: true }),
            anchor("bot"),
            "coin",
        ],
        "#": () => [
            sprite("steel"),
            area(),
            body({ isStatic: true }),
            //offscreen({ hide: true }),
            anchor("bot"),
        ],
        ">": () => [
            sprite("ghosty"),
            area(),
            anchor("bot"),
            body(),
            patrol(),
            //offscreen({ hide: true }),
            "enemy"
        ],
        /*"-": () => [
            sprite("grass"),
            area(),
            body({ isStatic: true }),
            // odd that the offscreen component causes the game to lag
            //offscreen({ hide: true }),
            anchor("bot"),
        ],*/
    },
}

const CONTROLSCHEMES = {
    wasd: { jump: "w", left: "a", right: "d", down: "s", icons: ["W", "A", "D", "S"], human: "WASD" },
    arrow: { jump: "up", left: "left", right: "right", down: "down", icons: ["↑", "←", "→", "↓"], human: "Arrow keys" },
}

var controlscheme = "arrow"

function bindkeys(scheme, player) {
    onKeyPress("space", () => {
        if (player.isGrounded()) {
            player.jump()
            player.play("jump")
        }
    })
    onKeyPress(scheme.jump, () => {
        if (player.isGrounded()) {
            player.jump()
            player.play("jump")
        }
    })

    onKeyDown(scheme.left, () => {
        player.move(-SPEED, 0)
        player.flipX = true
        if (player.isGrounded() && player.curAnim() !== "run") {
            player.play("run")
        }
    })

    onKeyDown(scheme.right, () => {
        player.move(SPEED, 0)
        player.flipX = false
        if (player.isGrounded() && player.curAnim() !== "run") {
            player.play("run")
        }
    })

    onKeyPress(scheme.down, () => {
        player.wie = 10
    })

    onKeyRelease(scheme.down, () => {
        player.mass = 1
    })

        ;[scheme.left, scheme.right].forEach((key) => {
            onKeyRelease(key, () => {
                // Only reset to "idle" if player is not holding any of these keys
                if (player.isGrounded() && !isKeyDown(scheme.left) && !isKeyDown(scheme.right)) {
                    player.play("idle")
                }
            })
        })
}

const music = play("happy", {
    loop: true,
    paused: false,
    volume: 0.5,
})

window.photo = false

function addfullscreenbtn() {
    const btn = add([
        sprite("fullscreen"),
        pos(),
        scale(1 / 18),
        fixed(),
        area(),
        onsize((x)=>{x.pos=vec2(width() - 512 / 18 - 8, height() - 512 / 18 - 8)}),
        "fullscreen",
        cursormod("pointer", 1 / 18, 1 / 18),
    ])
    if (document.fullscreenElement) {
        btn.play("big")
    } else {
        btn.play("small")
    }

    btn.onClick(() => {
        if (!document.fullscreenElement) {
            document.body.requestFullscreen()
            btn.play("big")
        } else {
            document.exitFullscreen()
            btn.play("small")
        }
    })

    return btn
}




scene("game", ({ levelIdx, score }) => {
    var startscore = score ??= 0;
    // Use the level passed, or first level
    const level = addLevel(LEVELS[levelIdx ??= 0], LEVELCFG)

    if (levelIdx === 0 && !photo) {
        add([
            text(`Use ${CONTROLSCHEMES[controlscheme].icons[1]} and ${CONTROLSCHEMES[controlscheme].icons[2]} to move`, { font: "pixel" }),
            pos(12),
            z(-1)
        ])
        add([
            text(`Use Space or ${CONTROLSCHEMES[controlscheme].icons[0]} to jump`, { font: "pixel" }),
            pos(vec2(200, -32)),
            z(-1)
        ])
    }

    if (levelIdx === 3 && !photo) {
        add([
            text("Jump on Ghosts\nto explode them,\nand launch yourself!", { font: "pixel" }),
            pos(vec2(0, 128)),
            z(-1)
        ])
    }

    // Get the player object from tag
    const player = level.get("player")[0]

    bindkeys(CONTROLSCHEMES[controlscheme], player)

    level.get("portal").forEach((x)=>x.play("spin"))
    level.get("coin").forEach((x,i) => setTimeout(() => x.play("move"), i*50))

    player.play("idle")


    player.onGround((obj) => {
        if (!obj.is("coin")) play("jumpland")
        if (!isKeyDown("left") && !isKeyDown("right")) {
            player.play("idle")
        } else {
            player.play("run")
        }
    })

    player.onCollide("coin", (coin) => {
        destroy(coin)
        play("coin")
        score++
        scoreLabel.text = score
    })

    player.onGround((l) => {
        if (l.is("enemy")) {
            player.jump(SPEED * 3)
            destroy(l)
            addKaboom(player.pos)
        }
    })
    player.onCollide("enemy", (e, col) => {
        // if it's not from the top, die
        if (!col.isBottom()) {
            go("lose", { levelIdx: levelIdx, score: startscore })
        }
    })

    player.onCollide("danger", (x) => {
        go("lose", { levelIdx: levelIdx, score: startscore })
    })

    let curTweenpos = null
    let curTweenscale = null

    function gotocam() {
        if (curTweenpos) curTweenpos.cancel()
        if (curTweenscale) curTweenscale.cancel()
        // start the tween
        curTweenscale = tween(
            // start value (accepts number, Vec2 and Color)
            camScale(),
            // destination value
            vec2(Math.max(player.vel.y,0)*-0.00005+0.8,Math.max(player.vel.y,0)*-0.00005+0.8),
            // duration (in seconds)
            0.5,
            // how value should be updated
            (val) => camScale(val),
            // interpolation function (defaults to easings.linear)
            easings.easeOutExpo,
        )
        curTweenpos = tween(
            // start value (accepts number, Vec2 and Color)
            camPos(),
            // destination value
            player.pos,
            // duration (in seconds)
            0.5,
            // how value should be updated
            (val) => camPos(val),
            // interpolation function (defaults to easings.linear)
            easings.easeOutExpo,
        )
    }
    player.onUpdate(() => {
        // center camera to player
        gotocam()
        // check fall death
        if (player.pos.y >= height() * 2) {
            go("lose", { levelIdx: levelIdx, score: startscore })
        }
        if (!player.isGrounded()) {
            player.play("jump")
        }
    })
    player.onPhysicsResolve(() => {
        gotocam()
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
    const scorecoin = add([
        sprite("coin"),
        pos(vec2(0)),
        fixed(),
    ])
    scorecoin.play("move")
    const scoreLabel = add([
        text(score, {
            size: 46,
            font: "pixel"
        }),
        pos(vec2(64, 12)),
        fixed(),
    ])
    if (photo) {
        scorecoin.hidden = true
        scoreLabel.hidden = true
    }

    onKeyPress(() => play('empty'))
    onKeyPress("r", () => {
        go("game", {
            levelIdx: 0,
            score: 0,
        })
    })
    onKeyPress("escape", () => go("menu", { levelIdx: levelIdx, score: startscore }))
    addfullscreenbtn()
})



function start() {
    // Start with the "game" scene, with initial parameters
    go("game", {
        levelIdx: 0,
        score: 0,
    })
}

scene("lose", (x) => {
    add([
        text("Press space to restart level\nPress R to restart game", { align: "center" }),
        pos(),
        onsize((x)=>{x.pos = center()}),
        anchor("center")
    ])
    add([
        text("You Lose!", { align: "center", font: "pixel", size: 72 }),
        pos(),
        onsize((x)=>{x.pos = center().sub(vec2(0, 72))}),
        anchor("center")
    ])
    onKeyPress("escape", () => go("menu"))
    addKaboom(center(), { scale: 20 })
    onClick(() => go("game", x))
    onKeyPress("space", () => go("game", x))
    onKeyPress("r", start)
    addfullscreenbtn()
})
scene("win", ({score}) => {
    add([
        text(`You got ${score} of 20 coins!\nPress Space to restart`, { align: "center" }),
        pos(),
        onsize((x)=>{x.pos = center()}),
        anchor("center")
    ])
    add([
        text("You Win!", { align: "center", font: "pixel", size: 72 }),
        pos(),
        onsize((x)=>{x.pos = center().sub(vec2(0, 72))}),
        anchor("center")
    ])
    onKeyPress("escape", () => go("menu"))
    onKeyPress("space", start)
    onClick(start)
    addfullscreenbtn()
})
scene("menu", (x) => {
    add([
        text("IF THE MUSIC INS'T PLAYING, CLICK THE PAGE", {
            align: "center",
            size: 16,
            font: "pixel",
        }),
        pos(),
        onsize((x)=>{x.pos = vec2(center().x, 16)}),
        anchor("center")
    ])

    const title = add([
        text("Stickman Jump Game", {
            align: "center",
            size: 72,
            font: "pixel",
        }),
        pos(),
        onsize((x)=>{x.pos = center().sub(vec2(0, 128))}),
        anchor("center")
    ])
    title.onUpdate(() => {
        title.pos = center().sub(vec2(0, 128 + easings.easeInOutCubic((Math.sin(time())+1)/2) * 32)) // brain is confused by this
    })
    onKeyPress(() => play('empty'))
    onClick(() => play('empty'))
    addButton("Play", (x)=>x.pos = center(), () => { setCursor("default"); go("game", x ?? JSON.parse(localStorage.getItem("platformersave")) ?? { levelIdx: 0, score: 0 }) })
    addButton("Settings", (x)=>x.pos = center().add(vec2(0, 96)), () => { go("settings") })
    addButton("Credits", (x)=>x.pos = center().add(vec2(0, 96*2)), () => { go("credits") })
    if (document.getElementById('main').dataset.exitbtn == "true") {addButton("Exit", (x)=>x.pos = center().add(vec2(0, 96*3)), () => {location.assign('/') })}
    addfullscreenbtn()
});

scene("settings", (x) => {
    onKeyPress("escape", () => go("menu"))
    let xmove = 0;
    onResize(()=>{if (height() < 1500) {
        xmove = -(height()/2 - 256);
        console.log(xmove)
    }})
    if (height() < 1500) {
        xmove = -(height()/2 - 256);
        console.log(xmove)
    }
    add([
        text("Settings", {
            align: "center",
            size: 72,
            font: "pixel",
        }),
        pos(),
        onsize((x)=>x.pos=center().sub(vec2(0, 128-xmove))),
        anchor("center")
    ])
    addButton("Back", (x)=>x.pos=center().add(vec2(0, 256+xmove)), () => { go("menu", x) })
    addButton("Music\nOn/Off", (x)=>x.pos=center().add(vec2(0, xmove)), () => {
        music.paused = !music.paused
    }, "Toggle Music")
    addButton(controlscheme == "wasd" ? "Switch to\nArrow keys" : "Switch to\nWASD", (x)=>x.pos=center().add(vec2(0, 96+xmove)), (btn) => {
        controlscheme = (controlscheme == "wasd" ? "arrow" : "wasd")
        btn.children[0].text = controlscheme == "wasd" ? "Switch to\nArrow keys" : "Switch to\nWASD"
    }, "Switch\ncontrol scheme")
    addfullscreenbtn()
})
scene("credits", () => {
    add([
        text("Credits", {
            align: "center",
            size: 72,
            font: "pixel",
        }),
        pos(),
        onsize((x)=>x.pos=center().sub(vec2(0, 128))),
        anchor("center")
    ])
    let y = 0;
    for (const [key, value] of Object.entries(credits)) {
        let x = add([
            text(`${key}: ${value}`, { align: "center", font: "pixel", size: 20, width: width() }),
            pos(),
            area(),
            onsize((x)=>x.pos=center().add(vec2(0, x.ymove-32))),
            anchor("center"),
            cursormod("pointer", 1.2),
            {ymove: y},
        ])
        x.onClick(() => {window.open(value)})
        y += 40
    }
    addButton("Back", (x)=>x.pos=center().add(vec2(0, 256)), () => { go("menu") })
    addfullscreenbtn()
})

go("menu")
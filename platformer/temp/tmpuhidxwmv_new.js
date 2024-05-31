// Please note that this file is not meant to be run on its own. It is meant to be imported into other files.


/**
 * Creates a tooltip object with the specified text.
 * @param {string} txt - The text to display in the tooltip.
 * @returns {object} - The tooltip object.
 */
export function tooltip(txt) {
    return {
        id: "tooltip",
        require: ["pos", "area"],
        add() {
            this.hovertween = null;
            this.onHover(() => {
                let formattxt = formatText({
                    text: txt,
                    font: "pixel",
                });

                this.tooltipObj = add([
                    rect(formattxt.width/2+64, formattxt.height / 2 + 24, { radius: 8 }),
                    pos(mousePos().add(vec2(0, 32))),
                    area(),
                    scale(1),
                    color(0, 0, 0),
                ]);

                this.tooltipObj.add([
                    text(txt, { font: "pixel" }),
                    color(255, 255, 255),
                    pos(12, 8)
                ]);
            });
            this.onHoverUpdate(() => {
                let curTween = this.hovertween;
                if (curTween) curTween.cancel();
                // start the tween
                curTween = tween(
                    // start value (accepts number, Vec2 and Color)
                    this.tooltipObj.pos,
                    // destination value
                    mousePos().add(vec2(0, 32)),
                    // duration (in seconds)
                    0.2,
                    // how value should be updated
                    (val) => this.tooltipObj.pos = val,
                    // interpolation function (defaults to easings.linear)
                    easings.easeOutExpo
                );
            });
            this.onHoverEnd(() => {
                destroy(this.tooltipObj);
            });
        },
    };
}
/**
 * Creates a patrol behavior for game objects.
 * @param {number} speed - The speed at which the object moves.
 * @param {number} dir - The direction in which the object moves (-1 for left, 1 for right).
 * @returns {Object} - The patrol behavior object.
 */
export function patrol(speed = 60, dir = 1) {
    return {
        id: "patrol",
        require: ["pos", "area"],
        add() {
            this.on("collide", (obj, col) => {
                if ((col.isLeft() || col.isRight()) && !obj.is("player")) {
                    dir = -dir;
                }
            });
        },
        update() {
            this.move(speed * dir, 0);
            this.flipX = dir < 0;
        },
    };
}
/**
 * Creates a resize handler that calls the provided function when the window size changes.
 * @param {Function} func - The function to be called when the window size changes.
 * @returns {Object} - An object with properties and methods related to the resize handler.
 */
export function onsize(func) {
    return {
        id: 'resizehandler',
        require: ['pos'],
        add() {
            onResize(() => {
                func(this);
            });
            func(this);
        }
    };
}
/**
 * Creates and returns a button element with the specified text, position, function, and optional hover tooltip.
 *
 * @param {string} txt - The text to display on the button.
 * @param {object} p - The position of the button.
 * @param {function} f - The function to execute when the button is clicked.
 * @param {string} [hover] - Optional tooltip to display when hovering over the button.
 * @returns {object} - The created button element.
 */
export function addButton(txt, p, f, hover) {

    let x = [
        rect(420, 80, { radius: 8 }),
        pos(),
        area(),
        scale(1),
        anchor("center"),
        outline(4),
        cursormod("pointer", 1.2),
        onsize(p)
    ];
    if (hover) x.push(tooltip(hover));


    // add a parent background object
    const btn = add(x);


    btn.add([
        text(txt, { font: "pixel", align: "center" }),
        anchor("center"),
        color(0, 0, 0),
    ]);


    btn.onClick((...args) => f.call(btn, btn, ...args));

    return btn;

}

/**
 * A utility function that creates a cursor modifier object.
 * @param {string} c - The cursor type.
 * @param {number} [scale=1] - The scale of the cursor.
 * @param {number} [basescale=1] - The base scale of the cursor.
 * @returns {Object} - The cursor modifier object.
 */
export function cursormod(c, scale = 1, basescale = 1) {
    return {
        requires: ["pos", "area"],
        id: "cursormod",
        add() {
            /**
             * Event handler for when the cursor is hovered over.
             * Sets the cursor scale and type.
             */
            this.onHover(() => {
                this.scale = vec2(scale);
                setCursor(c);
            });

            /**
             * Event handler for when the cursor is no longer hovered over.
             * Resets the cursor scale and type to default.
             */
            this.onHoverEnd(() => {
                this.scale = vec2(basescale);
                setCursor("default");
            });
        }
    };
}

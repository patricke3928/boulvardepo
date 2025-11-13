const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];
const numParticles = 100;

function random(min, max) { return Math.random() * (max - min) + min; }

class Particle {
    constructor() {
        this.x = random(0, canvas.width);
        this.y = random(0, canvas.height);
        this.vx = random(-0.5, 0.5);
        this.vy = random(-0.5, 0.5);
        this.radius = random(1, 3);
    }
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, 2*Math.PI);
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.fill();
    }
    update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
    }
}

for(let i=0; i<numParticles; i++) { particles.push(new Particle()); }

function animate() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

animate();

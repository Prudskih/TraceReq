const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

video.addEventListener("play", () => {

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  function draw(){
    ctx.drawImage(video,0,0);

    const frame = ctx.getImageData(0,0,canvas.width,canvas.height);
    const data = frame.data;

    for(let i=0;i<data.length;i+=4){

      const r = data[i];
      const g = data[i+1];
      const b = data[i+2];

      if(g > 150 && r < 120 && b < 120){
        data[i+3] = 0;
      }
    }

    ctx.putImageData(frame,0,0);
    requestAnimationFrame(draw);
  }

  draw();
});
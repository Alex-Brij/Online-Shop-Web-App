// window.onload is optional since it depends on the way in which you fire events
window.onload=function(){

    // selecting the elements for which we want to add a tooltip
    const target = document.getElementById("name");
    const tooltip = document.getElementById("tooltip-text");

    // change display to 'block' on mouseover
    target.addEventListener('mouseover', () => {
    tooltip.style.display = 'block';
    }, false);

    // change display to 'none' on mouseleave
    target.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
    }, false);

}
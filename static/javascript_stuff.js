// window.onload is optional since it depends on the way in which you fire events
window.onload=function(){

    function information_popup(target, popup) {
        // selecting the elements for which we want to add a tooltip
        let target = document.getElementById(target);
        let tooltip = document.getElementById(popup);

        // change display to 'block' on mouseover
        target.addEventListener('mouseover', () => {tooltip.style.display = 'block';}, false);

        // change display to 'none' on mouseleave
        target.addEventListener('mouseleave', () => {tooltip.style.display = 'none';}, false);

    }

    information_popup("name", "popup1")


}

let setUpToolTip = function() {
    let tooltip = "",
        toolTipDiv = document.querySelector(".div-tooltip"),
        toolTipElements = document.querySelectorAll(".hover-tooltip");
}
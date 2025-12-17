$(document).ready(function() {
	
	// hide expand button when sidebar visible
	const sidebar = document.getElementById("sidebarContainer");
	const openBtn = document.getElementById("btnExpandSidebar");

	if (sidebar && openBtn) {
	      sidebar.addEventListener("shown.bs.collapse", () => {
	        openBtn.style.display = "none";
	      });
	      sidebar.addEventListener("hidden.bs.collapse", () => {
	        openBtn.style.display = "inline-block";
	      });

	      // set initial state on page load
	      openBtn.style.display = sidebar.classList.contains("show")
	        ? "none"
	        : "inline-block";
 	 }
	 
	 
	 // select2
	 $(".tagging-select").each(function() {
	   $(this).select2({
	     tokenSeparators: [','],  // Split input on commas
	     placeholder: "any",
	   });
	 });
});
from django.shortcuts import render

# custom 404 view
def not_found_404(request, exception):
    return render(request, '404.html', status=404)

def server_error_500(request, exception):
    return render(request, '500.html', status=500)

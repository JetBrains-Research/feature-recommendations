docker build -t recommendations:latest .
kubectl delete deployment recommendations
kubectl run recommendations --image=recommendations:latest --port=80 --image-pull-policy=Never
kubectl delete service recommendations
kubectl expose deployment recommendations --type=LoadBalancer
kubectl get pods
kubectl port-forward pod/recommendations-<ID>  5000:5000
# This function demonstrates a trojan-like behavior for educational purposes.
# It provides a simple calculator and has a hidden action that logs usage to a file.

def calculator():
	print("Simple Calculator")
	x = int(input("Enter first number: "))
	y = int(input("Enter second number: "))
	print("Result:", x + y)

def hidden_action():
	"""
	Logs the usage of the calculator to 'trojan_log.txt' and prints a notification.
	"""
	with open("trojan_log.txt", "a") as f:
		f.write("Calculator used.\n")
	print("[!] Hidden action executed (writing to trojan_log.txt)")

if __name__ == "__main__":
	calculator()
	conceal_hidden = True  # Change to True to execute hidden_action
	if conceal_hidden:
		hidden_action()

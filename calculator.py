import tkinter as tk
import math

def on_click(button_text):
    """Handle button clicks for calculator operations"""
    if button_text == 'C':
        # Clear function: reset the display
        display.delete(0, tk.END)
    elif button_text == '=':
        try:
            expression = display.get()
            
            # Replace ^ with ** for exponentiation using Python's power operator
            expression = expression.replace('^', '**')
            
            # Evaluate the expression
            result = eval(expression)
            
            # Clear display and show result
            display.delete(0, tk.END)
            display.insert(0, str(result))
        except ZeroDivisionError:
            # Handle division by zero specifically
            display.delete(0, tk.END)
            display.insert(0, "Error: Division by Zero")
        except SyntaxError:
            display.delete(0, tk.END)
            display.insert(0, "Error: Invalid Syntax")
        except Exception as e:
            display.delete(0, tk.END)
            display.insert(0, "Error")
    else:
        # Append button text to display
        display.insert(tk.END, button_text)

# Create the main window
root = tk.Tk()
root.title("CSC426 Calculator")
root.geometry("400x500")

# Create the display entry field
display = tk.Entry(root, width=20, font=('Arial', 24), justify='right', borderwidth=2, relief='solid')
display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')

# Define button layout: numbers, operators (+, -, /, *, ^, %, C)
buttons = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['0', 'C', '=', '+'],
    ['^', '%', '.', 'sqrt']
]

# Create buttons in grid layout
for row_idx, row_buttons in enumerate(buttons, start=1):
    for col_idx, button_text in enumerate(row_buttons):
        if button_text == 'sqrt':
            # Special handling for sqrt button
            btn = tk.Button(root, text=button_text, font=('Arial', 16), bg='#FFB347',
                          command=lambda: on_sqrt_click())
        elif button_text in ['=', 'C']:
            # Highlight operation buttons
            btn = tk.Button(root, text=button_text, font=('Arial', 18), bg='#90EE90',
                          command=lambda text=button_text: on_click(text))
        elif button_text in ['+', '-', '*', '/', '^', '%']:
            # Highlight operator buttons
            btn = tk.Button(root, text=button_text, font=('Arial', 18), bg='#87CEEB',
                          command=lambda text=button_text: on_click(text))
        else:
            # Regular number and decimal buttons
            btn = tk.Button(root, text=button_text, font=('Arial', 18),
                          command=lambda text=button_text: on_click(text))
        btn.grid(row=row_idx, column=col_idx, sticky='nsew', padx=5, pady=5)

def on_sqrt_click():
    """Handle square root button click with error handling"""
    try:
        value = float(display.get())
        if value < 0:
            display.delete(0, tk.END)
            display.insert(0, "Error: Negative Number")
        else:
            result = math.sqrt(value)
            display.delete(0, tk.END)
            display.insert(0, str(result))
    except ValueError:
        display.delete(0, tk.END)
        display.insert(0, "Error: Invalid Input")
    except Exception:
        display.delete(0, tk.END)
        display.insert(0, "Error")

# Configure grid weights for responsive, resizable UI
for i in range(6):
    root.grid_rowconfigure(i, weight=1)
for i in range(4):
    root.grid_columnconfigure(i, weight=1)

# Start the calculator application
root.mainloop()

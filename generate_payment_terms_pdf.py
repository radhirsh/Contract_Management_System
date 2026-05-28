from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Output PDF path
output_path = "payment_terms_60days.pdf"

# Create a PDF with payment terms > 60 days
def create_payment_terms_pdf(path):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30 * mm, height - 40 * mm, "Contract Document")
    c.setFont("Helvetica", 12)
    c.drawString(30 * mm, height - 60 * mm, "Section: Payment Terms")
    c.setFont("Helvetica", 11)
    c.drawString(30 * mm, height - 75 * mm, "The payment terms for this contract are 75 days from the date of invoice.")
    c.save()

if __name__ == "__main__":
    create_payment_terms_pdf(output_path)
    print(f"PDF generated: {output_path}")

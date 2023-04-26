from db.model import Base, sa, GUID
from sqlalchemy.orm import relationship


class Review(Base):
    __tablename__ = "review"

    comment = sa.Column(sa.String(255), nullable=True)
    rating = sa.Column(sa.Integer, default=0)
    reviewed = sa.Column(sa.Boolean, default=False)
    edit_limit = sa.Column(sa.Integer, default=0)
    user_id = sa.Column(GUID, sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    user = relationship(
        "User",
        foreign_keys=[user_id],
    )
    product_id = sa.Column(GUID, sa.ForeignKey("product.id"))
    product = relationship("Product", foreign_keys=[product_id])

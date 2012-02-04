/* Copyright 2012 the SumatraPDF project authors (see AUTHORS file).
   License: Simplified BSD (see COPYING.BSD) */

#ifndef MuiCss_h
#define MuiCss_h

// This is only meant to be included by Mui.h inside mui namespace

namespace css {

enum PropType {
    PropFontName = 0,       // font-family
    PropFontSize,           // font-size
    PropFontWeight,         // font-weight
    PropPadding,            // padding
    PropColor,              // color
    PropBgColor,            // background-color

    PropBorderTopWidth,     // border-top-width
    PropBorderRightWidth,   // border-right-width
    PropBorderBottomWidth,  // border-bottom-width
    PropBorderLeftWidth,    // border-left-width

    PropBorderTopColor,     // border-top-color
    PropBorderRightColor,   // border-right-color
    PropBorderBottomColor,  // border-bottom-color
    PropBorderLeftColor,    // border-left-color

    PropTextAlign,          // text-align

    PropsCount              // must be at the end!
};

bool IsWidthProp(PropType type);
bool IsColorProp(PropType type);

enum ColorType {
    ColorSolid,
    ColorGradientLinear,
    // TODO: other gradient types?
};

struct ColorDataSolid {
    Brush * cachedBrush;
    ARGB    color;
};

struct ColorDataGradientLinear {
    LinearGradientMode  mode;
    ARGB                startColor;
    ARGB                endColor;
};

struct ColorData {
    ColorType   type;
    union {
        ColorDataSolid          solid;
        ColorDataGradientLinear gradientLinear;
    };

    bool operator==(const ColorData& other) const;
};

struct Padding {
    int top, right, bottom, left;
    bool operator ==(const Padding& other) const {
        return (top == other.top) &&
               (right == other.right) &&
               (bottom == other.bottom) &&
               (left == other.left);
    }
};

struct Prop {

    Prop(PropType type) : type(type) {}

    void Free();

    PropType    type;

    union {
        const WCHAR *   fontName;
        float           fontSize;
        FontStyle       fontWeight;
        Padding         padding;
        ColorData       color;
        float           width;
        AlignAttr       textAlign;
    };

    bool Eq(const Prop* other) const;

    static Prop *AllocFontName(const TCHAR *name);
    static Prop *AllocFontSize(float size);
    static Prop *AllocFontWeight(FontStyle style);
    // TODO: add AllocTextAlign(const char *s);
    static Prop *AllocTextAlign(AlignAttr align);
    static Prop *AllocPadding(int top, int right, int bottom, int left);
    static Prop *AllocColorSolid(PropType type, ARGB color);
    static Prop *AllocColorSolid(PropType type, int a, int r, int g, int b);
    static Prop *AllocColorSolid(PropType type, int r, int g, int b);
    static Prop *AllocColorSolid(PropType type, const char *color);
    static Prop *AllocColorLinearGradient(PropType type, LinearGradientMode mode, ARGB startColor, ARGB endColor);
    static Prop *AllocColorLinearGradient(PropType type, LinearGradientMode mode, const char *startColor, const char *endColor);
    static Prop *AllocWidth(PropType type, float width);
};

class Style {
    // if property is not found here, we'll search the
    // inheritance chain
    Style *     inheritsFrom;
    // generation number, changes every time we change the style
    size_t      gen;

public:
    Style(Style *inheritsFrom=NULL) : inheritsFrom(inheritsFrom) {
        gen = 1; // so that we can use 0 for NULL
    }

    Vec<Prop*>  props;

    void Set(Prop *prop);

    // shortcuts for setting multiple properties at a time
    void SetBorderWidth(float width);
    void SetBorderColor(ARGB color);

    Style * GetInheritsFrom() const;
    size_t GetIdentity() const;
};

#if 0 // TODO: maybe use that for convenience 
struct BorderWidth {
    int top, right, bottom, left;
};

struct BorderColors {
    ColorData   top, right, bottom, left;
};

// CachedStyle gathers values of all 
struct CachedStyle {
    const TCHAR *   fontName;
    float           fontSize;
    FontStyle       fontWeight;
    Padding         padding;
    ColorData       color;
    ColorData       bgColor;
    BorderWidth     borderWidth;
    BorderColors    borderColors;
    AlignAttr       textAlign;
};
#endif

class WrappedBrush {
public:
    bool    shouldDelete;
    Brush * brush;

    WrappedBrush(Brush *brush, bool shouldDelete) :
        brush(brush), shouldDelete(shouldDelete) {
    }
    ~WrappedBrush() {
        if (shouldDelete)
            ::delete brush;
    }
};

// globally known properties for elements we know about
// we fill them with default values and they can be
// modified by an app for global visual makeover
extern Style *gStyleDefault;
extern Style *gStyleButtonDefault;
extern Style *gStyleButtonMouseOver;

void   Initialize();
void   Destroy();

Font * CachedFontFromCachedProps(Prop **props);

Prop ** CachePropsForStyle(Style *style1, Style *style2);

WrappedBrush BrushFromProp(Prop *p, const Rect& r);
WrappedBrush BrushFromProp(Prop *p, const RectF& r);

} // namespace css

#endif

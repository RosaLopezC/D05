from django.utils import timezone
from django.contrib import admin
from .models import Categoria, Producto, Proveedor, Vendedor, Cliente, Venta, DetalleVenta
from django.db.models import Sum
from django.http import HttpResponse
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django import forms
from django.contrib import messages

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pub_date')
    list_filter = ('pub_date',)
    search_fields = ('nombre',)


class PrecioFilter(admin.SimpleListFilter):
    title = 'Rango de precios'
    parameter_name = 'precio_rango'

    def lookups(self, request, model_admin):
        return (
            ('0-5', '0 a 5'),
            ('6-10', '6 a 10'),
            ('11-15', '11 a 15'),
            ('16-20', '16 a 20'),
            ('21+', 'Más de 20'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-5':
            return queryset.filter(precio__gte=0, precio__lte=5)
        if self.value() == '6-10':
            return queryset.filter(precio__gte=6, precio__lte=10)
        if self.value() == '11-15':
            return queryset.filter(precio__gte=11, precio__lte=15)
        if self.value() == '16-20':
            return queryset.filter(precio__gte=16, precio__lte=20)
        if self.value() == '21+':
            return queryset.filter(precio__gt=20)
        return queryset


class InicialApellidoFilter(admin.SimpleListFilter):
    title = 'Inicial del apellido'
    parameter_name = 'inicial_apellido'

    def lookups(self, request, model_admin):
        letras = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        return [(letra, letra) for letra in letras]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(apellido__istartswith=self.value())
        return queryset


class AnioNacimientoFilter(admin.SimpleListFilter):
    title = 'Año de nacimiento'
    parameter_name = 'anio_nacimiento'

    def lookups(self, request, model_admin):
        anios = [(str(anio), str(anio)) for anio in range(1970, 2006)]
        return anios

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_nacimiento__year=self.value())
        return queryset


class MesNacimientoFilter(admin.SimpleListFilter):
    title = 'Mes de nacimiento'
    parameter_name = 'mes_nacimiento'

    def lookups(self, request, model_admin):
        meses = [(i, f"{i:02d}") for i in range(1, 13)]
        return meses

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_nacimiento__month=self.value())
        return queryset


class BaseAdmin(admin.ModelAdmin):
    actions = ['export_to_excel']
    change_list_template = "admin/change_list_with_import.html"

    def export_to_excel(modeladmin, request, queryset):
        import pandas as pd
        from django.http import HttpResponse

        df = pd.DataFrame(list(queryset.values()))
        for column in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
            df[column] = df[column].dt.tz_localize(None)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=data.xlsx'
        df.to_excel(response, index=False)
        return response

    export_to_excel.short_description = "Exportar a Excel"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_from_excel), name='import_data'),
        ]
        return custom_urls + urls

    def import_from_excel(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            filepath = fs.url(filename)

            df = pd.read_excel(filepath)

            for _, row in df.iterrows():
                if self.model == Venta:
                    Venta.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'cliente_id': row['cliente_id'],
                            'vendedor_id': row['vendedor_id'],
                            'fecha_venta': row['fecha_venta'],
                            'total_venta': row['total_venta'],
                        }
                    )
                elif self.model == DetalleVenta:
                    DetalleVenta.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'venta_id': row['venta_id'],
                            'producto_id': row['producto_id'],
                            'cantidad_vendida': row['cantidad_vendida'],
                            'precio_unitario': row['precio_unitario'],
                        }
                    )
                elif self.model == Producto:
                    Producto.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'nombre': row['nombre'],
                            'precio': row['precio'],
                            'categoria_id': row['categoria_id'],
                            'stock': row['stock'],
                            'pub_date': row['pub_date'],
                        }
                    )
                elif self.model == Cliente:
                    Cliente.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'nombre': row['nombre'],
                            'apellido': row['apellido'],
                            'dni': row['dni'],
                            'telefono': row['telefono'],
                            'direccion': row['direccion'],
                            'email': row['email'],
                            'fecha_nacimiento': row['fecha_nacimiento'],
                            'pub_date': row['pub_date'],
                        }
                    )
                elif self.model == Proveedor:
                    Proveedor.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'nombre': row['nombre'],
                            'contacto_nombre': row['contacto_nombre'],
                            'contacto_telefono': row['contacto_telefono'],
                            'contacto_email': row['contacto_email'],
                            'direccion': row['direccion'],
                        }
                    )
                elif self.model == Vendedor:
                    Vendedor.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'nombre': row['nombre'],
                            'apellido': row['apellido'],
                            'telefono': row['telefono'],
                            'email': row['email'],
                        }
                    )

            self.message_user(request, "Datos importados exitosamente.")
            return redirect(request.path_info)

        return render(request, 'admin/import.html', {'opts': self.model._meta})

class FechaVencimientoFilter(admin.SimpleListFilter):
    title = 'Vencimiento'
    parameter_name = 'vencimiento'

    def lookups(self, request, model_admin):
        return (
            ('vencidos', 'Vencidos'),
            ('pronto', 'Pronto a vencer (próximo mes)'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        next_month = today.replace(month=today.month + 1 if today.month < 12 else 1)
        if self.value() == 'vencidos':
            return queryset.filter(fecha_vencimiento__lt=today)
        if self.value() == 'pronto':
            return queryset.filter(fecha_vencimiento__range=[today, next_month])
        return queryset

class AñoVencimientoFilter(admin.SimpleListFilter):
    title = 'Año de vencimiento'
    parameter_name = 'año_vencimiento'

    def lookups(self, request, model_admin):
        current_year = timezone.now().year
        years = [(str(year), str(year)) for year in range(2018, current_year + 1)]
        years.insert(0, ('antes_2018', '2018 o antes'))
        return years

    def queryset(self, request, queryset):
        if self.value() == 'antes_2018':
            return queryset.filter(fecha_vencimiento__lt='2018-01-01')
        if self.value():
            return queryset.filter(fecha_vencimiento__year=self.value())
        return queryset

class MesVencimientoFilter(admin.SimpleListFilter):
    title = 'Mes de vencimiento'
    parameter_name = 'mes_vencimiento'

    def lookups(self, request, model_admin):
        meses = [(str(i), i) for i in range(1, 13)]
        return meses

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_vencimiento__month=self.value())
        return queryset

class PublicacionAñoFilter(admin.SimpleListFilter):
    title = 'Año de publicación'
    parameter_name = 'año_publicacion'

    def lookups(self, request, model_admin):
        current_year = timezone.now().year
        years = [(str(year), str(year)) for year in range(2018, current_year + 1)]
        years.insert(0, ('antes_2018', '2018 o antes'))
        return years

    def queryset(self, request, queryset):
        if self.value() == 'antes_2018':
            return queryset.filter(pub_date__year__lt=2018)
        if self.value():
            return queryset.filter(pub_date__year=self.value())
        return queryset

class PublicacionMesFilter(admin.SimpleListFilter):
    title = 'Mes de publicación'
    parameter_name = 'mes_publicacion'

    def lookups(self, request, model_admin):
        meses = [(str(i), i) for i in range(1, 13)]
        return meses

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(pub_date__month=self.value())
        return queryset

def actualizar_stock_fijo(modeladmin, request, queryset):
    nuevo_stock = 100  
    queryset.update(stock=nuevo_stock)  

actualizar_stock_fijo.short_description = 'Actualizar stock a 100'

def establecer_stock_cero(modeladmin, request, queryset):
    queryset.update(stock=0)  

establecer_stock_cero.short_description = 'Establecer stock a 0 (sin stock)'

class Stock0Filter(admin.SimpleListFilter):
    title = 'Productos con Stock 0'
    parameter_name = 'stock_0'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Con Stock 0'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(stock=0)
        return queryset

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'precio', 'stock', 'proveedor', 'fecha_vencimiento', 'pub_date')
    search_fields = ('nombre', 'descripcion','stock')
    list_filter = ('proveedor', FechaVencimientoFilter, AñoVencimientoFilter, MesVencimientoFilter, PublicacionAñoFilter, PublicacionMesFilter, Stock0Filter,PrecioFilter)

    actions = [actualizar_stock_fijo, establecer_stock_cero]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

class ProveedorAdmin(BaseAdmin):
    list_display = ('nombre', 'contacto_nombre', 'contacto_telefono', 'contacto_email', 'direccion')
    search_fields = ('nombre', 'contacto_nombre', 'direccion',)
    list_filter = ('direccion',)


class VendedorAdmin(BaseAdmin):
    list_display = ('nombre', 'apellido', 'telefono', 'email')
    search_fields = ('nombre', 'apellido', 'telefono', 'email',)
    list_filter = (InicialApellidoFilter,)


class ClienteAdmin(BaseAdmin):
    list_display = ('nombre', 'apellido', 'dni', 'telefono', 'direccion', 'email', 'fecha_nacimiento', 'pub_date')
    list_filter = ('apellido', 'pub_date', InicialApellidoFilter, AnioNacimientoFilter, MesNacimientoFilter)
    search_fields = ('nombre', 'apellido', 'dni', 'direccion',)


class VentaAdmin(BaseAdmin):
    list_display = ('cliente', 'vendedor', 'fecha_venta', 'total_venta')
    list_filter = ('fecha_venta',)
    search_fields = ('cliente__nombre', 'cliente__apellido', 'vendedor__nombre', 'vendedor__apellido',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(total_venta_calculado=Sum('detalleventa__precio_unitario'))


class DetalleVentaAdmin(BaseAdmin):
    list_display = ('venta', 'producto', 'cantidad_vendida', 'precio_unitario')
    search_fields = ('venta__cliente__nombre', 'producto__nombre',)
    list_filter = ('venta__fecha_venta',)


admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Proveedor, ProveedorAdmin)
admin.site.register(Vendedor, VendedorAdmin)
admin.site.register(Venta, VentaAdmin)
admin.site.register(DetalleVenta, DetalleVentaAdmin)

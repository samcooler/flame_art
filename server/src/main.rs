use kiss3d::light::Light;
use kiss3d::window::Window;
use nalgebra::{Point3, Translation3, UnitQuaternion, Vector3};
use rand::random;

fn main() {
    let c0: f32 = 5f32.sqrt() / 4.;
    let c1: f32 = (5. + 5f32.sqrt()) / 8.;
    let c2: f32 = (5. + 3. * 5f32.sqrt()) / 8.;
    let z: f32 = 0.;

    let vertices: [Vector3<f32>; 32] = [
        [c1, z, c2].into(),
        [c1, z, -c2].into(),
        [-c1, z, c2].into(),
        [-c1, z, -c2].into(),
        [c2, c1, z].into(),
        [c2, -c1, z].into(),
        [-c2, c1, z].into(),
        [-c2, -c1, z].into(),
        [z, c2, c1].into(),
        [z, c2, -c1].into(),
        [z, -c2, c1].into(),
        [z, -c2, -c1].into(),
        [z, c0, c2].into(),
        [z, c0, -c2].into(),
        [z, -c0, c2].into(),
        [z, -c0, -c2].into(),
        [c2, z, c0].into(),
        [c2, z, -c0].into(),
        [-c2, z, c0].into(),
        [-c2, z, -c0].into(),
        [c0, c2, z].into(),
        [c0, -c2, z].into(),
        [-c0, c2, z].into(),
        [-c0, -c2, z].into(),
        [c1, c1, c1].into(),
        [c1, c1, -c1].into(),
        [c1, -c1, c1].into(),
        [c1, -c1, -c1].into(),
        [-c1, c1, c1].into(),
        [-c1, c1, -c1].into(),
        [-c1, -c1, c1].into(),
        [-c1, -c1, -c1].into(),
    ];

    let faces: [[usize; 4]; 30] = [
        [12, 0, 2, 14],
        [14, 0, 10, 26],
        [26, 0, 5, 16],
        [13, 1, 9, 25],
        [25, 1, 4, 17],
        [17, 1, 5, 27],
        [28, 2, 6, 18],
        [18, 2, 7, 30],
        [30, 2, 10, 14],
        [19, 3, 6, 29],
        [29, 3, 9, 13],
        [13, 3, 1, 15],
        [20, 4, 8, 24],
        [24, 4, 0, 16],
        [16, 4, 5, 17],
        [18, 7, 6, 19],
        [19, 7, 3, 31],
        [31, 7, 11, 23],
        [22, 8, 6, 28],
        [28, 8, 2, 12],
        [12, 8, 0, 24],
        [29, 9, 6, 22],
        [22, 9, 8, 20],
        [20, 9, 4, 25],
        [30, 10, 7, 23],
        [23, 10, 11, 21],
        [21, 10, 5, 26],
        [31, 11, 3, 15],
        [15, 11, 1, 27],
        [27, 11, 5, 21],
    ];

    // face_center_vecs.

    let mut window = Window::new("Light Curve Simulator");
    faces.iter().for_each(|face| {
        let mut q = window.add_quad_with_vertices(
            face.iter()
                .map(|vertex_index| Point3::<f32>::from(vertices[*vertex_index]))
                .collect::<Vec<_>>()
                .as_slice(),
            2,
            2,
        );
        q.set_color(random(), random(), random());
    });

    let mut c = window.add_cube(1.0, 1.0, 1.0);
    let mut s = window.add_sphere(0.5);
    let mut p = window.add_cone(0.5, 1.0);
    let mut y = window.add_cylinder(0.5, 1.0);
    let mut a = window.add_capsule(0.5, 1.0);

    c.set_color(random(), random(), random());
    s.set_color(random(), random(), random());
    p.set_color(random(), random(), random());
    y.set_color(random(), random(), random());
    a.set_color(random(), random(), random());

    c.append_translation(&Translation3::new(2.0, 0.0, 0.0));
    s.append_translation(&Translation3::new(4.0, 0.0, 0.0));
    p.append_translation(&Translation3::new(-2.0, 0.0, 0.0));
    y.append_translation(&Translation3::new(-4.0, 0.0, 0.0));
    a.append_translation(&Translation3::new(0.0, 0.0, 0.0));

    window.set_light(Light::StickToCamera);

    let rot = UnitQuaternion::from_axis_angle(&Vector3::y_axis(), 0.014);

    while window.render() {
        c.append_rotation_wrt_center(&rot);
        s.append_rotation_wrt_center(&rot);
        p.append_rotation_wrt_center(&rot);
        y.append_rotation_wrt_center(&rot);
        a.append_rotation_wrt_center(&rot);
    }
}
